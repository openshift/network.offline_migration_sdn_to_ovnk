#!/usr/bin/python

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
        network_type=dict(type="str", required=True),  # Target network type
        timeout=dict(type="int", required=False, default=60),  # Timeout in seconds
    )

    module = AnsibleModule(argument_spec=module_args)

    network_type = module.params["network_type"]

    try:
        patch_command = f'oc patch Network.config.openshift.io cluster --type=merge --patch "{{\\"spec\\":{{\\"networkType\\":\\"{network_type}\\"}}}}"'
        result, error = run_command_with_retries(patch_command)
        if not error:
            module.exit_json(changed=True, msg=f"Successfully triggered {network_type} deployment.", output=result)
    except Exception as e:
        module.fail_json(msg=str(e))


if __name__ == "__main__":
    main()
