#!/usr/bin/python

# Copyright (c) 2025, Red Hat
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)


DOCUMENTATION = r"""
---
module: wait_for_mco_completion
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


def run_command(module, command):
    """Run a shell command safely using module.run_command and return output or error."""
    rc, stdout, stderr = module.run_command(command)

    if rc == 0:
        return stdout.strip(), None  # ✅ Success

    return None, f"❌ Command '{' '.join(command)}' failed: {stderr.strip()}"


def wait_for_mco(module, timeout):
    """Wait until MCO conditions are satisfied or timeout."""
    start_time = time.time()
    interval = 10

    while time.time() - start_time < timeout:
        module.warn("Checking MCO status...")

        # ✅ Run commands separately instead of chaining with `&&`
        commands = [
            ["oc", "wait", "mcp", "--all", "--for=condition=UPDATED=True", "--timeout=60s"],
            ["oc", "wait", "mcp", "--all", "--for=condition=UPDATING=False", "--timeout=60s"],
            ["oc", "wait", "mcp", "--all", "--for=condition=DEGRADED=False", "--timeout=60s"],
        ]

        errors = []
        for command in commands:
            output, error = run_command(module, command)
            if error:
                errors.append(error)

        if not errors:
            module.warn("✅ MCO is in the desired state.")
            return True

        module.warn(f"Retrying in {interval} seconds... Errors: {errors}")
        time.sleep(interval)

    return False  # Timeout reached


def main():
    module_args = dict(
        timeout=dict(type="int", required=False, default=2700),  # Timeout in seconds
    )

    module = AnsibleModule(argument_spec=module_args)

    timeout = module.params["timeout"]

    try:
        if wait_for_mco(module, timeout):
            module.exit_json(changed=False, msg="✅ MCO finished successfully.")
        else:
            module.fail_json(msg="❌ Timeout reached while waiting for MCO to finish.")
    except Exception as ex:
        module.fail_json(msg=f"Unexpected error: {str(ex)}")


if __name__ == "__main__":
    main()
