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
    patch_master_cmd = [
        "oc", "patch", "MachineConfigPool", "master", "--type=merge", "--patch",
        json.dumps(patch)
    ]
    patch_worker_cmd = [
        "oc", "patch", "MachineConfigPool", "worker", "--type=merge", "--patch",
        json.dumps(patch)
    ]

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
