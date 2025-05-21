# Copyright (c) 2025, Red Hat
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)


DOCUMENTATION = r"""
---
module: resume_mcp
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


def run_command(module, command):
    """Run a shell command safely using module.run_command and return output or raise an error."""
    rc, stdout, stderr = module.run_command(command)

    if rc == 0:
        return stdout.strip(), None  # Success

    return None, f"Command '{' '.join(command)}' failed: {stderr.strip()}"


def main():
    module_args = dict(
        timeout=dict(type="int", default=1800),
        sleep_interval=dict(type="int", default=10),
    )

    module = AnsibleModule(argument_spec=module_args, supports_check_mode=True)

    timeout = module.params["timeout"]
    sleep_interval = module.params["sleep_interval"]

    # Patch commands for MCPs
    patch = {"spec": {"paused": False}}
    patch_master_cmd = ["oc", "patch", "MachineConfigPool", "master", "--type=merge", "--patch", json.dumps(patch)]
    patch_worker_cmd = ["oc", "patch", "MachineConfigPool", "worker", "--type=merge", "--patch", json.dumps(patch)]

    end_time = time.time() + timeout

    while time.time() < end_time:
        master_output, master_error = run_command(module, patch_master_cmd)
        worker_output, worker_error = run_command(module, patch_worker_cmd)

        if not master_error and not worker_error:
            module.exit_json(changed=True, msg="Successfully resumed master and worker MCPs.")

        time.sleep(sleep_interval)

    module.fail_json(msg="Failed to resume MCPs within the timeout period.")


if __name__ == "__main__":
    main()
