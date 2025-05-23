# Copyright (c) 2025, Red Hat
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)


DOCUMENTATION = r"""
---
module: verify_cluster_operators_health
short_description: Verify if all cluster operators are healthy.
version_added: "1.0.0"
author: Miheer Salunke (@miheer)
description:
  - Verify if all cluster operators are healthy.
options:
  max_timeout:
    description: Max timeout for retrying the status of cluster operators.
    type: int
    required: false
    default: 2700
  pause_between_checks:
    description: Delay between the oc command checks for cluster operator availability.
    type: int
    required: false
    default: 30
  required_success_count:
    description: Number of times to execute the loop for the checking the availability of operators.
    type: int
    required: false
    default: 3
  checks:
    description: List of oc commands to check the cluster operator availability.
    required: true
    type: list
    elements: str
"""
EXAMPLES = r"""
- name: Check all cluster operators back to normal
  network.offline_migration_sdn_to_ovnk.verify_cluster_operators_health:
    max_timeout: 2700
    pause_between_checks: 30
    required_success_count: 3
    checks: "{{ post_rollback_checks }}"
  register: result
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


def check_cluster_operators(module, checks):
    """Check the status of cluster operators efficiently."""

    for check in checks:
        output, error = run_command(module, check)
        if error:
            return False, error  # ❌ Some condition failed
    return True, "✅ Cluster operators meet required conditions."


def main():
    module = AnsibleModule(
        argument_spec=dict(
            max_timeout=dict(type="int", required=False, default=2700),  # ⏳ Default timeout
            pause_between_checks=dict(type="int", required=False, default=30),
            required_success_count=dict(type="int", required=False, default=3),
            checks=dict(type="list", elements="str", required=True),
        )
    )

    max_timeout = module.params["max_timeout"]
    pause_between_checks = module.params["pause_between_checks"]
    required_success_count = module.params["required_success_count"]
    checks = module.params["checks"]

    start_time = time.time()
    success_count = 0

    while time.time() - start_time < max_timeout:
        success, message = check_cluster_operators(module, checks)

        if success:
            success_count += 1
            module.warn(f"✅ Check passed {success_count}/{required_success_count} times.")

            if success_count >= required_success_count:
                module.exit_json(changed=True, msg="✅ All checks passed successfully.")

            time.sleep(pause_between_checks)  # 💤 Only wait if more checks are needed

        else:
            module.warn(f"❌ Cluster check failed: {message}")
            success_count = 0  # Reset success count on failure
            time.sleep(10)  # Retry after failure

    module.fail_json(msg="❌ Timeout reached before cluster operators met the required conditions.")


if __name__ == "__main__":
    main()
