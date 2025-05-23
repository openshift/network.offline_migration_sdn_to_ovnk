# Copyright (c) 2025, Red Hat
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)


DOCUMENTATION = r"""
---
module: wait_for_mco
short_description: Checks if mcp's have started UPDATING.
version_added: "1.0.0"
author: Miheer Salunke (@miheer)
description:
  -  Checks if mcp's have started UPDATING.
options:
  timeout:
    description: Timeout in seconds.
    required: true
    type: int
"""
EXAMPLES = r"""
- name: Wait until MCO starts applying new machine config to nodes
  network.offline_migration_sdn_to_ovnk.wait_for_mco:
    timeout: "{{ migration_mco_timeout }}"
  register: mco_status
"""
RETURN = r"""
changed:
  description: Whether the CR was modified.
  type: bool
  returned: always
"""

from ansible.module_utils.basic import AnsibleModule
import time


def run_command(module, command):
    """Run a shell command safely using module.run_command and return output or raise an error."""
    rc, stdout, stderr = module.run_command(command)

    if rc == 0:
        return stdout.strip(), None  # Success

    return None, f"Command '{' '.join(command)}' failed: {stderr.strip()}"


def wait_for_mco(module, timeout):
    """Wait until the MCO starts applying the new machine config."""
    start_time = time.time()
    while time.time() - start_time < timeout:
        command = "oc wait mcp --all --for='condition=UPDATING=True' --timeout=10s"
        _unused, error = run_command(module, command)
        if not error:
            return "MCO started updating nodes successfully."
        time.sleep(10)  # Check every 10 seconds
    return "Timeout waiting for MCO to start updating nodes."


def main():
    module = AnsibleModule(
        argument_spec=dict(
            timeout=dict(type="int", required=True),
        )
    )

    timeout = module.params["timeout"]

    result_message = wait_for_mco(module, timeout)
    if "Timeout" in result_message:
        module.fail_json(msg=result_message)
    else:
        module.exit_json(changed=False, msg=result_message)


if __name__ == "__main__":
    main()
