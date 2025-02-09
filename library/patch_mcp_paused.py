from ansible.module_utils.basic import AnsibleModule
import subprocess
import time


def run_command_with_retries(command, retries=3, delay=3):
    """Execute a shell command with retries on failure."""
    for attempt in range(retries):
        try:
            result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
            return result.stdout.strip(), None
        except subprocess.CalledProcessError as e:
            if attempt < retries - 1:
                time.sleep(delay)
            else:
                return None, f"Command failed after {retries} attempts: {e.stderr.strip()}"
    return None, "Unknown error"


def main():
    module_args = dict(
        pool_name=dict(type="str", required=True),
        paused=dict(type="bool", required=True),
    )

    module = AnsibleModule(argument_spec=module_args, supports_check_mode=True)

    pool_name = module.params["pool_name"]
    paused = module.params["paused"]

    # Build the patch command
    paused_value = "true" if paused else "false"
    patch_command = (
        f"oc patch MachineConfigPool {pool_name} --type='merge' "
        f"--patch '{{\"spec\":{{\"paused\":{paused_value}}}}}'"
    )

    # Execute the command
    if module.check_mode:
        module.exit_json(changed=True, msg=f"Check mode: would patch {pool_name} with paused={paused_value}.")

    _, error = run_command_with_retries(patch_command)
    if error:
        module.fail_json(msg=f"Failed to patch {pool_name}: {error}")

    module.exit_json(changed=True, msg=f"Successfully patched {pool_name} with paused={paused_value}.")


if __name__ == "__main__":
    main()
