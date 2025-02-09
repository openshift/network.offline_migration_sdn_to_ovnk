#!/usr/bin/python
from ansible.module_utils.basic import AnsibleModule
import time
import subprocess


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


def run_module():
    module = AnsibleModule(argument_spec={})
    command = "oc whoami"
    result, error = run_command_with_retries(command)
    if not error:
        if "system:admin" in result:
            module.exit_json(changed=False, message="Logged in as `system:admin`.")
        else:
            module.fail_json(msg="Not logged in as `system:admin`. Please switch to `system:admin`.")
    if error:
        module.fail_json(msg="Failed to execute `oc whoami`. Ensure `oc` client is configured correctly.")


if __name__ == "__main__":
    run_module()
