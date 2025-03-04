#!/usr/bin/python

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
        timeout=dict(type="int", default=120),  # Timeout in seconds
    )

    module = AnsibleModule(argument_spec=module_args)
    timeout = module.params["timeout"]

    try:

        patch = {"spec": {"migration": None }}
        # Patch the network operator
        patch_command = [
            "oc", "patch", "Network.operator.openshift.io", "cluster", "--type=merge",
            "--patch", json.dumps(patch)
        ]

        # Wait until migration field is cleared
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                output, error = run_command(module, patch_command)
                if error:
                    module.warn(f"Retrying as got an error: {error}")
                    time.sleep(3)
                    continue

                output, error = run_command(module, "oc get network -o yaml")
                if not error:
                    if "migration" not in output:
                        module.exit_json(changed=True, msg="Migration field cleared.")
                elif error:
                    module.warn(f"Retrying as got an error: {error}")
                    time.sleep(3)
            except Exception as ex:
                module.fail_json(msg=str(ex))

        module.fail_json(msg="Timeout waiting for migration field to be cleared.")
    except Exception as ex:
        module.fail_json(msg=str(ex))


if __name__ == "__main__":
    main()
