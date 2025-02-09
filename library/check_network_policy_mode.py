from ansible.module_utils.basic import AnsibleModule
import json
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


def check_network_policy_mode(module, timeout):
    """Check if the cluster is set to use NetworkPolicy isolation mode."""
    command = "oc get network.operator.openshift.io cluster -o json"

    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            output, error = run_command(command)
            if error:
                module.warn(f"Retrying as got an error: {error}")
                time.sleep(3)
            if not error:
                break
        except Exception as ex:
            module.fail_json(msg=str(ex))

    if output:
        network_config = json.loads(output)
        sdn_config = (
            network_config.get("spec", {})
            .get("defaultNetwork", {})
            .get("openshiftSDNConfig", {})
        )
        mode = sdn_config.get("mode", "unknown")
        return mode == "NetworkPolicy", mode
    return False, "unknown"


def main():
    module = AnsibleModule(
        argument_spec={"timeout": {"type": "int", "default": 120}, },
        supports_check_mode=True,
    )

    timeout = module.params["timeout"]

    try:
        is_network_policy, mode = check_network_policy_mode(module, timeout)
        if is_network_policy:
            module.exit_json(
                changed=False, msg="The cluster is correctly configured with NetworkPolicy isolation mode in the spec.defaultNetwork.openshiftConfig."
            )
        elif mode == "unknown" or mode == '':
            module.exit_json(
                msg="Could not determine the isolation mode. Please check your configuration. The default mode is NetworkPolicy")
        else:
            module.fail_json(
                msg=(
                    f"The cluster is not configured with NetworkPolicy isolation mode (current mode: '{mode}'). "
                    "OVNKubernetes supports only NetworkPolicy isolation mode. Please update your configuration."
                )
            )
    except Exception as e:
        module.fail_json(msg=str(e))


if __name__ == "__main__":
    main()
