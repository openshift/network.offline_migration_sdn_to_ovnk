#!/usr/bin/env bash
#
# Validate the collection with galaxy-importer *directly from the repo*
# (no separate tarball step).
#
# Mirrors the GitHub-Actions step:
#   python -m galaxy_importer.main --git-clone-path . --output-path /tmp
#

###############################################################################
# CONFIG
###############################################################################
LOGFILE="${LOGFILE:-/logs/collection_ci.log}"

###############################################################################
# INTERNALS – no change required
###############################################################################
set -euo pipefail
log() { printf '%s %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$*" | tee -a "$LOGFILE"; }
trap 'log "❌ CI step failed (line ${LINENO}). See ${LOGFILE} for details."; exit 1' ERR

###############################################################################
# STEPS
###############################################################################
log "🚀  Starting galaxy-importer validation (git-clone-path mode)"

# 1️⃣  Configure galaxy-importer
GAL_CFG="$(mktemp)"
cat > "$GAL_CFG" <<'EOF'
[galaxy-importer]
CHECK_REQUIRED_TAGS=True
EOF
export GALAXY_IMPORTER_CONFIG="$GAL_CFG"

# 2️⃣  Run galaxy-importer directly on the working tree
log "🔍  Running galaxy-importer …"
python3.12 -m galaxy_importer.main --git-clone-path . --output-path /tmp | tee -a "$LOGFILE"
rc=${PIPESTATUS[0]}
if [[ $rc -ne 0 ]]; then
  log "❌ galaxy-importer failed with exit code $rc"
  exit "$rc"
fi

log "✅ Collection validated successfully by galaxy-importer"
exit 0
