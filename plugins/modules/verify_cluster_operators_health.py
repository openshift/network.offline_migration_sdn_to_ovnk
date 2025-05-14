#!/usr/bin/python

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
            return False, error # ❌ Some condition failed
    return True, "✅ Cluster operators meet required conditions."


def main():
    module = AnsibleModule(
        argument_spec=dict(
            max_timeout=dict(type="int", required=False, default=2700),  # ⏳ Default timeout
            pause_between_checks=dict(type="int", required=False, default=30),
            required_success_count=dict(type="int", required=False, default=3),
            checks=dict(type="list", required=True)
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
