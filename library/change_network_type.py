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
        network_type=dict(type="str", choices=["OVNKubernetes", "OpenShiftSDN"], required=True),  # Target network type
        timeout=dict(type="int", default=120),  # Timeout in seconds
    )

    module = AnsibleModule(argument_spec=module_args)

    timeout = module.params["timeout"]

    network_type = module.params["network_type"]

    # Validate network type
    if network_type not in ["OVNKubernetes", "OpenShiftSDN"]:
        return None, f"Invalid networkType '{network_type}'. Supported: 'OVNKubernetes', 'OpenShiftSDN'."

    try:
        # Construct the patch command

        patch = {"spec": {"migration": {"networkType": network_type}}}
        patch_command = [
            "oc", "patch", "Network.operator.openshift.io", "cluster", "--type=merge",
            "--patch", json.dumps(patch)
        ]

        # Execute the command
        run_command(module, patch_command)

        # Wait until migration field is cleared
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                output, error = run_command(module, "oc get network -o yaml")
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
