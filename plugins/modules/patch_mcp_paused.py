from ansible.module_utils.basic import AnsibleModule
import time
import json


def run_command_with_retries(module, command, retries=3, delay=3):
    """Execute a shell command with retries on failure."""
    for attempt in range(retries):
        rc, stdout, stderr = module.run_command(command)

        if rc == 0:
            return stdout.strip(), None  # Success

        if attempt < retries - 1:
            module.warn(f"Retrying in {delay} seconds due to error: {stderr.strip()}")
            time.sleep(delay)  # Wait before retrying
        else:
            return None, f"Command failed after {retries} attempts: {stderr.strip()}"

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
    paused_value = True if paused else False

    # Build the patch command
    patch = {"spec": {"paused": paused_value}}

    patch_command = [
        "oc", "patch", "MachineConfigPool", pool_name, "--type=merge", "--patch",
        json.dumps(patch)
    ]

    # Execute the command
    if module.check_mode:
        module.exit_json(changed=True, msg=f"Check mode: would patch {pool_name} with paused={paused_value}.")


    _, error = run_command_with_retries(module, patch_command)
    if error:
        module.fail_json(msg=f"Failed to patch {pool_name}: {error}")

    module.exit_json(changed=True, msg=f"Successfully patched {pool_name} with paused={paused_value}.")


if __name__ == "__main__":
    main()
