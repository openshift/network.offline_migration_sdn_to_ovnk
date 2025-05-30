# Copyright (c) 2025, Red Hat
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)


DOCUMENTATION = r"""
---
module: check_network_provider
short_description: Check if the CNI network provider is expected one.
version_added: "1.0.0"
author: Miheer Salunke (@miheer)
description:
  - Check if the CNI network provider is expected one.
options:
  expected_network_type:
    description: Check if the CNI network provider is expected one.
    type: str
    required: true
  timeout:
    description: Sets desired timeout
    type: int
    default: 120
"""
EXAMPLES = r"""
- name: Check the CNI network provider
  network.offline_migration_sdn_to_ovnk.check_network_provider:
    expected_network_type: "{{ post_migration_expected_network_type }}"
  register: result
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


def run_command(module, command):
    """Run a shell command safely using module.run_command and return output or raise an error."""
    rc, stdout, stderr = module.run_command(command)

    if rc == 0:
        return stdout.strip(), None  # Success

    return None, f"Command '{' '.join(command)}' failed: {stderr.strip()}"


def get_network_type(module, timeout):
    """Retrieve the current network type."""
    command = "oc get network.config/cluster -o json"
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            output, error = run_command(module, command)
            if not error:
                network_config = json.loads(output)
            elif error:
                module.warn(f"Retrying as got an error: {error}")
            time.sleep(3)
        except Exception as ex:
            module.fail_json(msg=str(ex))
    return network_config.get("status", {}).get("networkType", None)


def main():
    module = AnsibleModule(
        argument_spec={
            "expected_network_type": {"type": "str", "required": True},
            "timeout": {"type": "int", "default": 120},  # Timeout in seconds
        },
        supports_check_mode=True,
    )

    timeout = module.params["timeout"]
    expected_network_type = module.params["expected_network_type"]

    try:
        current_network_type = get_network_type(module, timeout)
        if current_network_type == expected_network_type:
            module.exit_json(
                changed=False,
                msg=f"The current network provider is {current_network_type}, as expected.",
                network_type=current_network_type,
            )
        else:
            module.fail_json(
                msg=f"Expected network provider {expected_network_type}, but found {current_network_type}.",
                network_type=current_network_type,
            )
    except Exception as e:
        module.fail_json(msg=str(e))


if __name__ == "__main__":
    main()
