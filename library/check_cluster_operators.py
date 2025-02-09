from ansible.module_utils.basic import AnsibleModule
import subprocess
import time


def run_oc_command(command):
    """Run the `oc` command and return its output."""
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        return True, result.stdout.strip()
    except subprocess.CalledProcessError as e:
        return False, e.stderr.strip()


def main():
    module_args = dict(
        timeout=dict(type="int", required=True),  # Total timeout in seconds
        interval=dict(type="int", required=False, default=10)  # Interval between retries
    )

    module = AnsibleModule(argument_spec=module_args, supports_check_mode=True)

    timeout = module.params["timeout"]
    interval = module.params["interval"]

    start_time = time.time()

    while time.time() - start_time < timeout:
        available_cmd = "oc wait co --all --for='condition=AVAILABLE=True' --timeout=60s"
        progressing_cmd = "oc wait co --all --for='condition=PROGRESSING=False' --timeout=60s"
        degraded_cmd = "oc wait co --all --for='condition=DEGRADED=False' --timeout=60s"

        available_status, available_output = run_oc_command(available_cmd)
        progressing_status, progressing_output = run_oc_command(progressing_cmd)
        degraded_status, degraded_output = run_oc_command(degraded_cmd)

        if available_status and progressing_status and degraded_status:
            # Print all cluster operators and their conditions
            get_co_cmd = "oc get co -o wide"
            _, co_output = run_oc_command(get_co_cmd)

            module.exit_json(
                changed=False,
                message="All ClusterOperators are in the desired state.",
                operators=co_output
            )
        else:
            time.sleep(interval)

    module.fail_json(msg="Timeout waiting for ClusterOperators to reach the desired state.")


if __name__ == "__main__":
    main()
