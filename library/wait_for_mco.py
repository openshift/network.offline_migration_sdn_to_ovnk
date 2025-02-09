#!/usr/bin/python

from ansible.module_utils.basic import AnsibleModule
import subprocess
import time


def run_command(command):
    """Run a shell command and return its output or raise an error."""
    try:
        result = subprocess.run(
            command, shell=True, text=True, capture_output=True, check=True
        )
        return result.stdout.strip(), None
    except subprocess.CalledProcessError as err:
        return None, Exception(f"Command '{command}' failed: {err.stderr.strip()}")


def wait_for_mco(timeout):
    """Wait until the MCO starts applying the new machine config."""
    start_time = time.time()
    while time.time() - start_time < timeout:
        command = "oc wait mcp --all --for='condition=UPDATING=True' --timeout=10s"
        _, error = run_command(command)
        if not error:
            return "MCO started updating nodes successfully."
        time.sleep(10)  # Check every 10 seconds
    return "Timeout waiting for MCO to start updating nodes."


def main():
    module = AnsibleModule(
        argument_spec=dict(
            timeout=dict(type="int", required=True),
        )
    )

    timeout = module.params["timeout"]

    result_message = wait_for_mco(timeout)
    if "Timeout" in result_message:
        module.fail_json(msg=result_message)
    else:
        module.exit_json(changed=False, msg=result_message)


if __name__ == "__main__":
    main()
