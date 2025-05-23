# Copyright (c) 2025, Red Hat
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)


DOCUMENTATION = r"""
---
module: delete_primary_nncp
short_description: If nncp is configured on primary interface then deletes it.
version_added: "1.0.0"
author: Miheer Salunke (@miheer)
description:
  - If nncp is configured on primary interface then deletes it.
options:
  interface_name:
    description: Provide the primary interface name.
    required: true
    type: str
  retries:
    description: Number of retries for the oc command.
    type: int
    default: 3
  delay:
    description: Delay between oc retries.
    type: int
    default: 3
"""
EXAMPLES = r"""
- name: Delete NNCP for primary interface if exists
  network.offline_migration_sdn_to_ovnk.delete_primary_nncp:
    interface_name: "{{ migration_interface_name }}"
  when:
    - interface_name is defined
    - interface_name | length > 0
    - crd_check
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
    for attempt in range(retries):
        rc, stdout, stderr = module.run_command(command)
        if rc == 0:
            return stdout.strip(), None
        module.warn(f"Attempt {attempt + 1} failed: {stderr.strip()}")
        time.sleep(delay)
    return None, f"Command '{' '.join(command)}' failed after {retries} attempts: {stderr.strip()}"


def main():
    module_args = dict(interface_name=dict(type="str", required=True), retries=dict(type="int", default=3), delay=dict(type="int", default=3))

    module = AnsibleModule(argument_spec=module_args)

    interface_name = module.params["interface_name"]
    retries = module.params["retries"]
    delay = module.params["delay"]

    # Step 0: Check if NMState Operator is installed (CRD must exist)
    check_crd_cmd = ["oc", "get", "crd", "nodenetworkconfigurationpolicies.nmstate.io", "-o", "name"]
    crd_output, crd_error = run_command_with_retries(module, check_crd_cmd, retries, delay)
    if crd_error or not crd_output.strip():
        module.exit_json(changed=False, skipped=True, msg="NMState Operator not installed or NNCP CRD is missing. Skipping deletion.")

    # Step 1: Get list of NNCPs
    get_command = ["oc", "get", "nncp", "-o", "json"]
    output, error = run_command_with_retries(module, get_command, retries, delay)
    if error:
        module.fail_json(msg=f"Failed to retrieve NNCPs: {error}")

    try:
        nncp_data = json.loads(output)
    except json.JSONDecodeError:
        module.fail_json(msg="Failed to parse NNCP JSON output.")

    target_nncp = None
    for item in nncp_data.get("items", []):
        name = item["metadata"]["name"]
        interfaces = item.get("spec", {}).get("desiredState", {}).get("interfaces", [])
        for iface in interfaces:
            if iface.get("name") == interface_name:
                target_nncp = name
                break
        if target_nncp:
            break

    if not target_nncp:
        module.exit_json(changed=False, msg=f"No NNCP found for interface '{interface_name}'.")

    # Step 2: Delete the NNCP
    delete_command = ["oc", "delete", "nncp", target_nncp]
    _unused, error = run_command_with_retries(module, delete_command, retries, delay)
    if error:
        module.fail_json(msg=f"Failed to delete NNCP '{target_nncp}': {error}")

    module.exit_json(changed=True, msg=f"NNCP '{target_nncp}' deleted successfully.")


if __name__ == "__main__":
    main()
