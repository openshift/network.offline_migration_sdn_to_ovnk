#!/bin/bash

# Enable strict error handling
set -euo pipefail

# Define variables
LOGFILE="cni_migration.log"
MIGRATION_PLAYBOOK="playbook-migration.yml"
ROLLBACK_PLAYBOOK="playbook-rollback.yml"

# Function to log output
log() {
    if [[ "$(uname)" == "Darwin" ]]; then
        # macOS (BSD date)
        TIMESTAMP=$(date "+%Y-%m-%d %H:%M:%S")
    else
        # Linux (GNU date)
        TIMESTAMP=$(date --utc "+%Y-%m-%d %H:%M:%S")
    fi
    echo "$TIMESTAMP - $1" | tee -a "$LOGFILE"
}

# Function to check if playbook exists
check_playbook() {
    if [[ ! -f "$1" ]]; then
        log "❌ Error: Playbook '$1' not found!"
        exit 1
    fi
}

# Function to get current CNI type
get_cni_type() {
    if ! CNI_TYPE=$(oc get Network.operator.openshift.io cluster -o jsonpath='{.spec.defaultNetwork.type}' 2>>"$LOGFILE"); then
        log "❌ Error: Failed to fetch CNI type from OpenShift."
        exit 1
    fi
    echo "$CNI_TYPE"
}

# Start logging
log "Checking current CNI type..."

# Get the current CNI type
CNI=$(get_cni_type)

# Check the CNI type and execute the appropriate playbook
if [[ "$CNI" == "OpenShiftSDN" ]]; then
    log "Detected CNI: OpenShiftSDN. Running migration playbook..."
    check_playbook "$MIGRATION_PLAYBOOK"  # Check if playbook exists

    # Run ansible-playbook and check for failures
    if ! ansible-playbook "$MIGRATION_PLAYBOOK" | tee -a "$LOGFILE"; then
        log "❌ Migration playbook failed or stopped unexpectedly!"
        exit 1
    fi
    log "✅ Migration playbook completed successfully."

elif [[ "$CNI" == "OVNKubernetes" ]]; then
    log "Detected CNI: OVNKubernetes. Running rollback playbook..."
    check_playbook "$ROLLBACK_PLAYBOOK"  # Check if playbook exists

    # Run ansible-playbook and check for failures
    if ! ansible-playbook "$ROLLBACK_PLAYBOOK" | tee -a "$LOGFILE"; then
        log "❌ Rollback playbook failed or stopped unexpectedly!"
        exit 1
    fi
    log "✅ Rollback playbook completed successfully."

else
    log "❌ Unknown CNI type detected: $CNI"
    exit 1
fi

log "✅ Script execution completed successfully."
exit 0
