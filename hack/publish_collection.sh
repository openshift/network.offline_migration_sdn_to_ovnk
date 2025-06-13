#!/usr/bin/env bash
# ------------------------------------------------------------------------------
# publish_ah.sh  —  Upload an Ansible collection tarball to Red Hat Automation Hub
#
# Requirements:
#   • ansible-core (for ansible-galaxy)
#   • Environment variable AH_TOKEN  (the Automation Hub token)
#        — or pass the token as the first positional argument
#
# Usage:
#   AH_TOKEN=xxxxx ./scripts/publish_ah.sh
#   ./scripts/publish_ah.sh xxxxx
# ------------------------------------------------------------------------------

set -euo pipefail

###############################################################################
# 1.  Resolve token
###############################################################################
TOKEN="${AH_TOKEN:-${1:-}}"

if [[ -z "$TOKEN" ]]; then
    echo "ERROR: Automation Hub token is required." >&2
    echo "Set AH_TOKEN env var or pass it as the first argument." >&2
    exit 1
fi

###############################################################################
# 2.  Locate tarball (assumes exactly ONE *.tar.gz in cwd)
###############################################################################
shopt -s nullglob
tarballs=( ./*.tar.gz )
shopt -u nullglob

if (( ${#tarballs[@]} == 0 )); then
    echo "ERROR: No collection tarball (*.tar.gz) found in current directory." >&2
    exit 1
elif (( ${#tarballs[@]} > 1 )); then
    echo "ERROR: Multiple tarballs found; please leave exactly one in the directory." >&2
    printf '  %s\n' "${tarballs[@]}"
    exit 1
fi

TARBALL="${tarballs[0]}"
echo "• Publishing ${TARBALL}"

###############################################################################
# 3.  Create temporary ansible.cfg with token (works on macOS + GNU/Linux)
###############################################################################
tmpdir=$(mktemp -d)                # always a directory
trap 'rm -rf "$tmpdir"' EXIT       # clean up on exit

cfg="$tmpdir/ansible.cfg"          # explicit, valid filename

cat > "$cfg" <<EOF
[galaxy]
server_list = rh_automation_hub

[galaxy_server.rh_automation_hub]
url = https://cloud.redhat.com/api/automation-hub/
auth_url = https://sso.redhat.com/auth/realms/redhat-external/protocol/openid-connect/token
token = ${TOKEN}
EOF

###############################################################################
# 4.  Publish
###############################################################################
ANSIBLE_CONFIG="$cfg" ansible-galaxy collection publish "$TARBALL"

echo "✓ Collection published successfully."

