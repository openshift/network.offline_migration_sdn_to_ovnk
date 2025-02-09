from ansible.module_utils.basic import AnsibleModule
import subprocess
import time


def run_command(command):
    """Run a shell command and return its output or error."""
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        return result.stdout.strip(), None
    except subprocess.CalledProcessError as e:
        return None, e.stderr.strip()


def main():
    module_args = dict(
        timeout=dict(type="int", default=1800),
        sleep_interval=dict(type="int", default=10),
    )

    module = AnsibleModule(argument_spec=module_args, supports_check_mode=True)

    timeout = module.params["timeout"]
    sleep_interval = module.params["sleep_interval"]

    # Patch commands for MCPs
    patch_master_cmd = (
        "oc patch MachineConfigPool master --type='merge' --patch '{\"spec\":{\"paused\":false}}'"
    )
    patch_worker_cmd = (
        "oc patch MachineConfigPool worker --type='merge' --patch '{\"spec\":{\"paused\":false}}'"
    )

    end_time = time.time() + timeout

    while time.time() < end_time:
        master_output, master_error = run_command(patch_master_cmd)
        worker_output, worker_error = run_command(patch_worker_cmd)

        if not master_error and not worker_error:
            module.exit_json(changed=True, msg="Successfully resumed master and worker MCPs.")

        time.sleep(sleep_interval)

    module.fail_json(msg="Failed to resume MCPs within the timeout period.")


if __name__ == "__main__":
    main()
