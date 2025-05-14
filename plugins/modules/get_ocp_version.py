#!/usr/bin/python

from ansible.module_utils.basic import AnsibleModule
import json
import time


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
        retries=dict(type="int", default=3),
        delay=dict(type="int", default=5),
    )

    module = AnsibleModule(argument_spec=module_args, supports_check_mode=True)

    retries = module.params["retries"]
    delay = module.params["delay"]

    command = "oc get clusterversion version -o json"

    stdout, error = run_command_with_retries(module, command, retries, delay)

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
