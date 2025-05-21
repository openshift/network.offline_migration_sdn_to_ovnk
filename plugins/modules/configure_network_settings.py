# Copyright (c) 2025, Red Hat
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)


DOCUMENTATION = r"""
---
module: change_network_settings
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
import time
import json


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


def run_patch_command(module, patch_command, retries, delay):
    """Execute the oc patch command with retries."""
    if module.check_mode:
        module.exit_json(changed=True, msg="Check mode: Patch command prepared", command=patch_command)

    try:
        output, error = run_command_with_retries(module, patch_command, retries=retries, delay=delay)
        if not error:
            module.exit_json(changed=True, msg="Network configuration patched successfully.", output=output)
        else:
            module.fail_json(msg=f"Patch command failed: {error}")
    except Exception as e:
        module.fail_json(msg=f"Unexpected error while executing patch command: {str(e)}")


def main():
    module = AnsibleModule(
        argument_spec={
            "configure_network_type": {"type": "str", "choices": ["ovnKubernetes", "openshiftSDN"], "required": True},
            "mtu": {"type": "int", "required": False},
            "geneve_port": {"type": "int", "required": False},
            "ipv4_subnet": {"type": "str", "required": False},
            "retries": {"type": "int", "default": 3},
            "delay": {"type": "int", "default": 5},
            "vxlanPort": {"type": "int", "required": False},
        },
        supports_check_mode=True,
    )

    network_type = module.params["configure_network_type"]
    mtu = module.params["mtu"]
    geneve_port = module.params["geneve_port"]
    ipv4_subnet = module.params["ipv4_subnet"]
    retries = module.params["retries"]
    delay = module.params["delay"]
    vxlanPort = module.params["vxlanPort"]

    # Ensure patching is needed
    if not any([mtu, geneve_port, ipv4_subnet, vxlanPort]):
        module.exit_json(changed=False, msg="No changes required. No valid parameters provided.")

    # Build the patch payload
    patch_data = {"spec": {"defaultNetwork": {f"{network_type}Config": {}}}}

    if network_type == "ovnKubernetes":
        if mtu:
            patch_data["spec"]["defaultNetwork"][f"{network_type}Config"]["mtu"] = mtu
        if geneve_port:
            patch_data["spec"]["defaultNetwork"][f"{network_type}Config"]["genevePort"] = geneve_port
        if ipv4_subnet:
            patch_data["spec"]["defaultNetwork"][f"{network_type}Config"]["v4InternalSubnet"] = ipv4_subnet
        if vxlanPort:
            module.warn("vxlanPort can't be set in ovnKubernetesConfig")
        # Prepare and execute patch command
        patch_command = f"oc patch Network.operator.openshift.io cluster --type=merge --patch '{json.dumps(patch_data)}'"
        run_patch_command(module, patch_command, retries, delay)

    elif network_type == "openshiftSDN":
        if mtu:
            patch_data["spec"]["defaultNetwork"][f"{network_type}Config"]["mtu"] = mtu
        if vxlanPort:
            patch_data["spec"]["defaultNetwork"][f"{network_type}Config"]["vxlanPort"] = vxlanPort
        if geneve_port or ipv4_subnet:
            module.warn("geneve_port or ipv4_subnet can't be set in openshiftSDNConfig")
        # Prepare and execute patch command
        patch_command = f"oc patch Network.operator.openshift.io cluster --type=merge --patch '{json.dumps(patch_data)}'"
        run_patch_command(module, patch_command, retries, delay)

    else:
        module.exit_json(changed=False, msg="No changes patched. No valid parameters provided.")


if __name__ == "__main__":
    main()
