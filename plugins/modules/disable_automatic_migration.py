#!/usr/bin/python

# Copyright (c) 2025, Red Hat
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)


DOCUMENTATION = r"""
---
module: disable_automatic_migration
short_description: Change the default network type (SDN ↔ OVN).
version_added: "1.0.0"
author: Miheer Salunke (@miheer)
description:
  - Switches the cluster DefaultNetwork between C(OpenShiftSDN)
    and C(OVNKubernetes) by patching the Network.operator CR.
options:
  new_type:
    description: Desired network type.
    choices: [OpenShiftSDN, OVNKubernetes]
    required: true
"""
EXAMPLES = r"""
- name: Migrate to OVN-K
  network.offline_migration_sdn_to_ovnk.change_network_type:
    new_type: OVNKubernetes
"""
RETURN = r"""
changed:
  description: Whether the CR was modified.
  type: bool
  returned: always
"""

from ansible.module_utils.basic import AnsibleModule
import json
import time


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


def patch_network(module, network_type, egress_ip, egress_firewall, multicast):
    """Patch the Network.operator.openshift.io cluster resource with generic networkType."""

    # Validate network type
    if network_type not in ["OVNKubernetes", "OpenShiftSDN"]:
        return None, f"Invalid networkType '{network_type}'. Supported: 'OVNKubernetes', 'OpenShiftSDN'."

    # Check if any field is set (prevent empty patch)
    if egress_ip is None and egress_firewall is None and multicast is None:
        return None, "No values provided. Automatic migration will be applied."

    if network_type == "OVNKubernetes":
        patch_data = {"spec": {"migration": {"networkType": network_type, "features": {}}}}
    elif network_type == "OpenShiftSDN":
        patch_data = {"spec": {"migration": {"features": {}}}}

    if egress_ip is not None:
        patch_data["spec"]["migration"]["features"]["egressIP"] = egress_ip
    if egress_firewall is not None:
        patch_data["spec"]["migration"]["features"]["egressFirewall"] = egress_firewall
    if multicast is not None:
        patch_data["spec"]["migration"]["features"]["multicast"] = multicast

    patch_command = f"oc patch Network.operator.openshift.io cluster --type='merge' --patch '{json.dumps(patch_data)}'"
    output, error = run_command_with_retries(module, patch_command, retries=3, delay=5)
    if error:
        return None, error
    return output, None


def main():
    module = AnsibleModule(
        argument_spec={
            "network_type": {"type": "str", "choices": ["OVNKubernetes", "OpenShiftSDN"], "required": True},  # Takes OpenShiftSDN or OVNKubernetes
            "egress_ip": {"type": "bool", "default": None},
            "egress_firewall": {"type": "bool", "default": None},
            "multicast": {"type": "bool", "default": None},
        },
        supports_check_mode=True,
    )

    network_type = module.params["network_type"]
    egress_ip = module.params["egress_ip"]
    egress_firewall = module.params["egress_firewall"]
    multicast = module.params["multicast"]

    # Patch the network operator
    output, error = patch_network(module, network_type, egress_ip, egress_firewall, multicast)
    if error:
        module.exit_json(changed=False, msg=error)

    module.exit_json(changed=True, msg=f"Network operator migration settings updated for {network_type}.", output=output)


if __name__ == "__main__":
    main()
