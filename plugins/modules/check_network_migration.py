# Copyright (c) 2025, Red Hat
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)


DOCUMENTATION = r"""
---
module: check_network_migration
short_description: Check if migration of cni was set to desired one i.e OpenShiftSDN or OVNKubernetes.
version_added: "1.0.0"
author: Miheer Salunke (@miheer)
description:
  - Check if migration of cni was set to desired one i.e OpenShiftSDN or OVNKubernetes.
options:
  expected_network_type:
    description: Checks for desired CNI set.
    required: true
    type: str
  max_retries:
    description: Retries for oc command.
    type: int
    required: false
    default: 3
  delay:
    description: Delay between retries for oc command
    type: int
    required: false
    default: 3
"""
EXAMPLES = r"""
- name: Check network migration status
  network.offline_migration_sdn_to_ovnk.check_network_migration:
    expected_network_type: "{{ network_type }}"
    max_retries: "{{ max_retries }}"
    delay: "{{ retry_delay }}"
  register: network_migration_result
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


def main():
    module_args = dict(
        expected_network_type=dict(type="str", required=True),  # Expected value (e.g., "OpenShiftSDN")
        max_retries=dict(type="int", default=3),  # Number of retries
        delay=dict(type="int", default=3),  # Delay between retries
    )

    module = AnsibleModule(argument_spec=module_args, supports_check_mode=True)

    command = ["oc", "get", "Network.config", "cluster", "-o", "json"]
    max_retries = module.params["max_retries"]
    delay = module.params["delay"]

    stdout, error = run_command_with_retries(module, command, retries=max_retries, delay=delay)

    if error:
        module.fail_json(msg=f"Failed to retrieve network config: {error}")

    try:
        network_config = json.loads(stdout)
        network_type = network_config.get("status", {}).get("migration", {}).get("networkType", "")

        if network_type == module.params["expected_network_type"]:
            module.exit_json(changed=False, msg=f"✅ Network migration type is correctly set to '{network_type}'.", network_type=network_type)
        else:
            module.fail_json(
                msg=f"❌ Network migration type is '{network_type}', expected '{module.params['expected_network_type']}'.", network_type=network_type
            )

    except json.JSONDecodeError:
        module.fail_json(msg="❌ Failed to parse network config JSON output.")


if __name__ == "__main__":
    main()
