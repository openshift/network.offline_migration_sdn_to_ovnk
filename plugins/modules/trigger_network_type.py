# Copyright (c) 2025, Red Hat
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

DOCUMENTATION = r"""
---
module: trigger_network_type
short_description: Change the OpenShift networkType (and optionally clusterNetwork CIDR/prefix).
version_added: "1.0.0"
author:
  - Miheer Salunke (@miheer)
description:
  - Patches the C(Network.config.openshift.io/cluster) custom resource to
    change the value of C(spec.networkType).
  - When both C(cidr) and C(prefix) are provided the module also replaces
    the first entry in C(spec.clusterNetwork) with the supplied values.
  - The task fails if the supplied CIDR overlaps any of the address blocks
    that OVN-Kubernetes reserves internally
    (``100.64.0.0/16``, ``169.254.169.0/29``, ``100.88.0.0/16``,
    ``fd98::/64``, ``fd69::/125`` and ``fd97::/64``).
  - Uses the ``oc patch`` CLI and retries transient failures automatically.
options:
  network_type:
    description:
      - Desired value for C(spec.networkType).
    type: str
    required: true
    choices: [OVNKubernetes, OpenShiftSDN]
  cidr:
    description:
      - Optional cluster network CIDR to apply together with the network
        type change.
      - Must not overlap any of the reserved CIDRs listed above.
    type: str
  prefix:
    description:
      - Host prefix length that accompanies C(cidr).
      - Required only when C(cidr) is supplied.
    type: int
  timeout:
    description:
      - Maximum time (in seconds) to wait for the ``oc patch`` command to
        succeed before the module fails.
    type: int
    default: 60
"""

EXAMPLES = r"""
# 1. Switch to OVN-Kubernetes without altering the existing clusterNetwork
- name: Trigger OVN-Kubernetes deployment
  network.offline_migration_sdn_to_ovnk.trigger_network_type:
    network_type: OVNKubernetes

# 2. Switch to OVN-Kubernetes *and* update the primary clusterNetwork block
- name: Trigger OVN-Kubernetes with a new CIDR
  network.offline_migration_sdn_to_ovnk.trigger_network_type:
    network_type: OVNKubernetes
    cidr: 10.128.0.0/14
    prefix: 23
    timeout: 120
"""

RETURN = r"""
changed:
  description: Whether the Network CR was modified.
  type: bool
  returned: always
msg:
  description: Human-readable status message.
  type: str
  returned: always
output:
  description: Raw stdout returned by the underlying ``oc patch`` command.
  type: str
  returned: when successful
"""

from ansible.module_utils.basic import AnsibleModule
import time
import json
import ipaddress


def run_command_with_retries(module, command, retries=3, delay=3):
    """Execute a shell command with retries on failure."""
    for attempt in range(retries):
        rc, stdout, stderr = module.run_command(command)

        if rc == 0:
            return stdout.strip(), None  # Success

        if attempt < retries - 1:
            module.warn(f"Retrying in {delay} seconds due to error: {stderr.strip()}")
            time.sleep(delay)  # Wait before retrying
        else:
            return None, f"Command failed after {retries} attempts: {stderr.strip()}"

    return None, "Unknown error"


# ─────────────────────────────────────────────────────────────
# ADD a reusable deny-list of networks that must not overlap
# ─────────────────────────────────────────────────────────────
FORBIDDEN_NETS = [
    ipaddress.ip_network("100.64.0.0/16"),
    ipaddress.ip_network("169.254.169.0/29"),
    ipaddress.ip_network("100.88.0.0/16"),
    ipaddress.ip_network("fd98::/64"),
    ipaddress.ip_network("fd69::/125"),
    ipaddress.ip_network("fd97::/64"),
]


# ─────────────────────────────────────────────────────────────
def _ensure_no_overlap(cidr):
    """Validate that *cidr* does not overlap any forbidden network."""
    new_net = ipaddress.ip_network(cidr, strict=False)
    for bad in FORBIDDEN_NETS:
        if new_net.overlaps(bad):
            raise ValueError(
                f"The provided migration_cidr ({cidr}) overlaps with "
                f"reserved network {bad}."
            )
# ─────────────────────────────────────────────────────────────


def _build_patch(cidr, prefix, network_type):
    """
    Render the JSON patch that oc will consume.

    NOTE: *prefix* arrives from Ansible already as an int (see argument_spec),
    so we no longer cast it with int().
    """
    if cidr and prefix is not None:
        return {
            "spec": {
                "clusterNetwork": [{
                    "cidr": cidr,
                    "hostPrefix": prefix,   # already int
                }],
                "networkType": network_type,
            }
        }
    return {"spec": {"networkType": network_type}}


def main():
    module_args = dict(
        cidr=dict(type="str", required=False),
        prefix=dict(type="int", required=False),
        network_type=dict(type="str", choices=["OVNKubernetes", "OpenShiftSDN"], required=True),  # Target network type
        timeout=dict(type="int", required=False, default=60),  # Timeout in seconds
    )

    module = AnsibleModule(argument_spec=module_args)

    network_type = module.params["network_type"]
    cidr = module.params["cidr"]
    prefix = module.params["prefix"]

    try:
        # Validate (if provided)
        if cidr:
            try:
                ipaddress.ip_network(cidr, strict=False)  # syntax check
            except ValueError as exc:
                module.fail_json(msg=f"Invalid CIDR '{cidr}': {exc}")
            try:
                _ensure_no_overlap(cidr)
            except ValueError as exc:
                module.fail_json(msg=str(exc))
        patch = _build_patch(cidr, prefix, network_type)
        patch_command = ["oc", "patch", "Network.config.openshift.io", "cluster", "--type=merge", "--patch", json.dumps(patch)]
        result, error = run_command_with_retries(module, patch_command)
        if not error:
            module.exit_json(changed=True, msg=f"Successfully triggered {network_type} deployment.", output=result)
    except Exception as e:
        module.fail_json(msg=str(e))


if __name__ == "__main__":
    main()
