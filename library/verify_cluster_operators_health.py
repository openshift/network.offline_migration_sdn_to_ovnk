#!/usr/bin/python

from ansible.module_utils.basic import AnsibleModule
import subprocess
import time


def run_command(command):
    """Run a shell command and return its output or raise an error."""
    try:
        result = subprocess.run(
            command, shell=True, text=True, capture_output=True, check=True
        )
        return result.stdout.strip(), None
    except subprocess.CalledProcessError as err:
        return None, Exception(f"Command '{command}' failed: {err.stderr.strip()}")


def check_cluster_operators(checks):
    """Check the status of cluster operators."""
    '''
    checks = [
        "oc wait co --all --for='condition=Available=True' --timeout=60s",
        "oc wait co --all --for='condition=Progressing=False' --timeout=60s",
        "oc wait co --all --for='condition=Degraded=False' --timeout=60s",
    ]
    '''
    for check in checks:
        output, error = run_command(check)
        if error:
            return False, error
    return True, "Cluster operators meet required conditions."


def main():
    module = AnsibleModule(
        argument_spec=dict(
            max_timeout=dict(type="int", required=False, default=2700),
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
        success, message = check_cluster_operators(checks)
        if success:
            success_count += 1
            if success_count >= required_success_count:
                module.exit_json(changed=True, msg="All checks passed successfully 3 times in a row.")
            time.sleep(pause_between_checks)
        else:
            success_count = 0  # Reset success count on failure
            time.sleep(10)

    module.fail_json(msg="Timeout reached before cluster operators met the required conditions.")


if __name__ == "__main__":
    main()
