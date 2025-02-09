#!/usr/bin/python

from ansible.module_utils.basic import AnsibleModule
import json
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
        retries=dict(type="int", default=3),
        delay=dict(type="int", default=5),
    )

    module = AnsibleModule(argument_spec=module_args, supports_check_mode=True)

    retries = module.params["retries"]
    delay = module.params["delay"]

    command = "oc get clusterversion version -o json"

    stdout, error = run_command_with_retries(command, retries, delay)

    if error:
        module.fail_json(msg=error)

    try:
        version_data = json.loads(stdout)
        ocp_version = version_data["status"]["history"][0]["version"]
        module.exit_json(changed=False, version=ocp_version)
    except (KeyError, json.JSONDecodeError) as e:
        module.fail_json(msg=f"Failed to parse OpenShift version: {str(e)}")


if __name__ == "__main__":
    main()
