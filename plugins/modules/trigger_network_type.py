# Copyright (c) 2025, Red Hat
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)


DOCUMENTATION = r"""
---
module: trigger_network_type
short_description: Patches the networkType in the Network.config.openshift.io.
version_added: "1.0.0"
author: Miheer Salunke (@miheer)
description:
  - Patches the networkType in the Network.config.openshift.io.
options:
  network_type:
    description: Desired network type.
    required: true
    type: str
  timeout:
    description: Timeout in seconds.
    required: false
    default: 60
    type: int
"""
EXAMPLES = r"""
- name: Trigger OpenshiftSDN deployment
  network.offline_migration_sdn_to_ovnk.trigger_network_type:
    network_type: "{{ rollback_network_type }}"
    timeout: "{{ rollback_sdn_co_timeout }}"
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


def main():
    module_args = dict(
        network_type=dict(type="str", required=True),  # Target network type
        timeout=dict(type="int", required=False, default=60),  # Timeout in seconds
    )

    module = AnsibleModule(argument_spec=module_args)

    network_type = module.params["network_type"]

    try:
        patch = {"spec": {"networkType": network_type}}
        patch_command = ["oc", "patch", "Network.config.openshift.io", "cluster", "--type=merge", "--patch", json.dumps(patch)]
        result, error = run_command_with_retries(module, patch_command)
        if not error:
            module.exit_json(changed=True, msg=f"Successfully triggered {network_type} deployment.", output=result)
    except Exception as e:
        module.fail_json(msg=str(e))


if __name__ == "__main__":
    main()
