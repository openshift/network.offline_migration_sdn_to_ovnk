#!/usr/bin/python

from ansible.module_utils.basic import AnsibleModule
import time
import subprocess


def run_command(command):
    """Run a shell command and return its output or raise an error."""
    try:
        result = subprocess.run(
            command, shell=True, text=True, capture_output=True, check=True
        )
        return result.stdout.strip(), None
    except subprocess.CalledProcessError as err:
        return None, Exception(f"Command '{command}' failed: {err.stderr.strip()}")


def main():
    module_args = dict(
        timeout=dict(type="int", default=120),  # Timeout in seconds
    )

    module = AnsibleModule(argument_spec=module_args)
    timeout = module.params["timeout"]

    try:
        # Patch the network operator
        patch_command = (
            "oc patch Network.operator.openshift.io cluster --type='merge' "
            "--patch '{\"spec\":{\"migration\":null}}'"
        )

        # Wait until migration field is cleared
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                output, error = run_command(patch_command)
                if error:
                    module.warn(f"Retrying as got an error: {error}")
                    time.sleep(3)
                    continue

                output, error = run_command("oc get network -o yaml")
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
