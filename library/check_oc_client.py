#!/usr/bin/python

from ansible.module_utils.basic import AnsibleModule
import shutil
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


def is_oc_binary_present():
    """Check if the oc binary exists in the system's PATH."""
    return shutil.which("oc") is not None


def main():
    module = AnsibleModule(argument_spec={})

    # Check if the binary exists
    if not is_oc_binary_present():
        module.fail_json(msg="The oc binary is not present in the system's PATH.")

    # Check if the binary works and get its version
    result, error = run_command_with_retries("oc version --client")
    if not error:
        is_installed = True

    if is_installed:
        module.exit_json(changed=False, version=result)
    else:
        module.fail_json(msg=f"The oc binary is present but not functional: {result}")


if __name__ == "__main__":
    main()
