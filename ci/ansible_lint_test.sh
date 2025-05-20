#!/usr/bin/env bash
#
# Build → install → lint the collection.
# Any failure aborts the pipeline with a helpful message.

###############################################################################
# CONFIG
###############################################################################
LOGFILE="${LOGFILE:-/logs/collection_ci.log}"            # artefact name

###############################################################################
# INTERNALS – normally no change required
###############################################################################
set -euo pipefail

# Pretty-print with timestamp
log() {
  printf '%s %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$*" | tee -a "$LOGFILE"
}

# Catch *any* command that exits non-zero
trap 'log "❌ CI step failed (line ${LINENO}). Check ${LOGFILE} for details."; exit 1' ERR

###############################################################################
# STEPS
###############################################################################
log "🚀  Starting collection CI pipeline"

# 1️⃣ Build
log "📦  Building the Ansible collection…"
ansible-galaxy collection build . --force | tee -a "$LOGFILE"

# 2️⃣ Determine the brand-new tarball name
# returns the lexicographically-last tarball or an empty string
TARBALL=$(find . -maxdepth 1 -type f -name 'network-offline_migration_sdn_to_ovnk-*.tar.gz' \
           -print | sort | tail -n 1)

if [[ -z "$TARBALL" ]]; then
  log "❌ No collection tarball found after build step!"
  exit 1
fi
log "🆕  Built artifact: $TARBALL"

# 3️⃣ Install it into the controller's default path
log "📥  Installing $TARBALL …"
ansible-galaxy collection install --force "./${TARBALL}" | tee -a "$LOGFILE"

log "🔍  Running ansible-lint --profile production …"
ansible-lint --profile production | tee -a "$LOGFILE"
rc=${PIPESTATUS[0]}
if [[ $rc -ne 0 ]]; then
  log "❌ ansible-lint failed with exit code $rc"
  exit "$rc"
fi

log "✅  Collection built, installed, and linted successfully"
exit 0
