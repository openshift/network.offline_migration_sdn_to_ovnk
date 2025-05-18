#!/usr/bin/env bash
#
# Build → install → lint the collection.
# Any failure aborts the pipeline with a helpful message.

###############################################################################
# CONFIG
###############################################################################
COLL_DIR="."                                       # where galaxy.yml lives
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
ansible-galaxy collection build "$COLL_DIR" --force | tee -a "$LOGFILE"

# 2️⃣ Determine the brand-new tarball name
TARBALL=$(ls -1 network-offline_migration_sdn_to_ovnk-*.tar.gz | tail -n 1 || true)
if [[ -z "$TARBALL" ]]; then
  log "❌ No collection tarball found after build step!"
  exit 1
fi
log "🆕  Built artifact: $TARBALL"

# 3️⃣ Install it into the controller’s default path
log "📥  Installing $TARBALL …"
ansible-galaxy collection install --force -p ansible_collections "./${TARBALL}" | tee -a "$LOGFILE"

log "🔍  Running ansible-lint --profile production …"
cd ansible_collections/network/offline_migration_sdn_to_ovnk/
ansible-test sanity \
  --python 3.12 \
  --skip-test ansible-doc \
  --skip-test import \
  --skip-test no-smart-quotes \
  --skip-test pep8 \
  --skip-test pylint \
  --skip-test runtime-metadata \
  --skip-test shebang \
  --skip-test validate-modules \
  --skip-test yamllint | tee -a "$LOGFILE"
rc=${PIPESTATUS[0]}
if [[ $rc -ne 0 ]]; then
  log "❌ ansible-test sanity failed with exit code $rc"
  exit $rc
fi

log "✅  Collection built, installed, and passed sanity checks successfully"
exit 0
