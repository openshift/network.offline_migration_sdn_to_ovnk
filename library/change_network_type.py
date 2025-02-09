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
        network_type=dict(type="str", required=True),  # Target network type
        timeout=dict(type="int", default=120),  # Timeout in seconds
    )

    module = AnsibleModule(argument_spec=module_args)

    timeout = module.params["timeout"]

    network_type = module.params["network_type"]

    try:
        # Construct the patch command
        patch_command = (
            f"oc patch Network.operator.openshift.io cluster --type='merge' "
            f"--patch '{{\"spec\":{{\"migration\":{{\"networkType\":\"{network_type}\"}}}}}}'"
        )

        # Execute the command
        run_command(patch_command)

        # Wait until migration field is cleared
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                output, error = run_command("oc get network -o yaml")
                if not error:
                    if network_type in output:
                        module.exit_json(changed=True, msg=f"Migration field set to networkType:{network_type}.")
                elif error:
                    module.warn(f"Retrying as got an error: {error}")
                time.sleep(3)

            except Exception as ex:
                module.fail_json(msg=str(ex))

        module.fail_json(msg=f"Network type could not be changed to {network_type}.")
    except Exception as ex:
        module.fail_json(msg=str(ex))


if __name__ == "__main__":
    main()
