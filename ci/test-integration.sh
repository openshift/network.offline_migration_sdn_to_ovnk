#!/usr/bin/env bash
###############################################################################
#  Part 1 – Build, install and verify the collection
###############################################################################
set -euo pipefail

# ── collection metadata (edit if you renamed namespace/name) ────────────────
COLL_NAMESPACE="network"
COLL_NAME="offline_migration_sdn_to_ovnk"

# ── build → install → verify ------------------------------------------------
build_and_install_collection() {
  local tarball

  if [[ $# -gt 0 && -f "$1" ]]; then
    # user supplied a pre-built artifact
    tarball="$1"
    echo "🔹 Using existing tarball: $tarball"
  else
    echo "🔧 Building collection from source …"
    tarball=$(ansible-galaxy collection build . | awk '/Created collection/ {print $NF}')
    echo "   → Built $tarball"
  fi

  echo "📦 Installing collection …"
  ansible-galaxy collection install "$tarball"

  echo "🔍 Verifying installation …"
  if ansible-galaxy collection list "${COLL_NAMESPACE}.${COLL_NAME}" \
    >/dev/null 2>&1; then
    echo "✅ ${COLL_NAMESPACE}.${COLL_NAME} successfully installed."
  else
    echo "❌ Collection installation failed!" >&2
    exit 1
  fi
}

# optional first argument = path to tarball
build_and_install_collection "${1:-}"

###############################################################################
#  Part 2 – Migration / rollback script (unchanged logic)
###############################################################################

# Enable strict error handling
set -euo pipefail

# Define variables
LOGFILE="cni_migration.log"
MIGRATION_PLAYBOOK="playbooks/playbook-migration.yml"
ROLLBACK_PLAYBOOK="playbooks/playbook-rollback.yml"

# Function to log output
log() {
    if [[ "$(uname)" == "Darwin" ]]; then
        TIMESTAMP=$(date "+%Y-%m-%d %H:%M:%S")
    else
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

# ── Migration / Rollback flow ───────────────────────────────────────────────
log "Checking current CNI type ..."
CNI=$(get_cni_type)

if [[ "$CNI" == "OpenShiftSDN" ]]; then
    log "Detected CNI: OpenShiftSDN. Running migration playbook ..."
    check_playbook "$MIGRATION_PLAYBOOK"
    if ! ansible-playbook "$MIGRATION_PLAYBOOK" | tee -a "$LOGFILE"; then
        log "❌ Migration playbook failed or stopped unexpectedly!"
        exit 1
    fi
    log "✅ Migration playbook completed successfully."

elif [[ "$CNI" == "OVNKubernetes" ]]; then
    log "Detected CNI: OVNKubernetes. Running rollback playbook ..."
    check_playbook "$ROLLBACK_PLAYBOOK"
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
