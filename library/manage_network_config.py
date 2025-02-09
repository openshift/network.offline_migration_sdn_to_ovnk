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


def patch_network_operator(module, timeout, network_provider_config):
    """Patch the Network operator configuration."""
    # command = f"oc patch Network.operator.openshift.io cluster --type='merge' --patch='{"spec": {"defaultNetwork": {network_provider_config}: null } }'"
    command = f"oc patch Network.operator.openshift.io cluster --type='merge' --patch '{{\"spec\":{{\"defaultNetwork\":{{\"{network_provider_config}\":null}}}}}}'"

    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            output, error = run_command(command)
            if error:
                module.warn(f"Retrying as got an error: {error}")
                time.sleep(3)
            if not error:
                return output
        except Exception as ex:
            module.fail_json(msg=str(ex))


def delete_namespace(module, timeout, namespace):
    """Delete a specified namespace."""
    command = f"oc delete namespace {namespace}"
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            output, error = run_command(command)
            if error:
                module.warn(f"Retrying as got an error: {error}")
                time.sleep(3)
            if not error:
                return output
        except Exception as ex:
            module.fail_json(msg=str(ex))


def main():
    module = AnsibleModule(
        argument_spec={
            "network_provider_config": {"type": "str", "required": True},
            "namespace": {"type": "str", "required": False},
            "timeout": {"type": "int", "default": 120},  # Timeout in seconds
        },
        supports_check_mode=True,
    )

    network_provider_config = module.params["network_provider_config"]
    namespace = module.params.get("namespace")
    timeout = module.params["timeout"]

    try:
        # Apply the patches to the Network operator configuration
        patch_network_operator(module, timeout, network_provider_config)

        # Delete the namespace if provided
        if namespace:
            delete_namespace(module, timeout, namespace)

        module.exit_json(
            changed=True,
            msg="Network configuration updated and namespace deleted if provided.",
        )

    except Exception as e:
        module.fail_json(msg=str(e))


if __name__ == "__main__":
    main()
