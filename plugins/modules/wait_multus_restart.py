#!/usr/bin/python

from ansible.module_utils.basic import AnsibleModule
import time


def run_command(module, command):
    """Run a shell command safely using module.run_command and return output or raise an error."""
    rc, stdout, stderr = module.run_command(command)

    if rc == 0:
        return stdout.strip(), None  # Success

    return None, f"Command '{' '.join(command)}' failed: {stderr.strip()}"


def wait_for_multus_pods(module, timeout):
    """Wait for the Multus pods to restart."""
    start_time = time.time()
    interval = 10

    while time.time() - start_time < timeout:
        try:
            command = "oc rollout status ds/multus -n openshift-multus"
            output, error = run_command(module, command)
            if not error:
                if "successfully rolled out" in output:
                    return True
        except Exception as e:
            print(f"Retrying due to error: {str(e)}")
        time.sleep(interval)

    # Timeout reached
    return False


def main():
    module_args = dict(
        timeout=dict(type="int", required=False, default=300),  # Timeout in seconds
    )

    module = AnsibleModule(argument_spec=module_args)

    timeout = module.params["timeout"]

    try:
        if wait_for_multus_pods(module, timeout):
            module.exit_json(changed=False, msg="Multus pods restarted successfully.")
        else:
            module.fail_json(msg="Timeout reached while waiting for Multus pods to restart.")
    except Exception as ex:
        module.fail_json(msg=str(ex))


if __name__ == "__main__":
    main()
