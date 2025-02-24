#!/usr/bin/python

from ansible.module_utils.basic import AnsibleModule
import subprocess
import json
import time


def run_command_with_retries(command, retries=3, delay=5):
    """Runs a shell command with retries on failure."""
    for attempt in range(retries):
        try:
            result = subprocess.run(command, shell=True, text=True, capture_output=True, check=True)
            return result.stdout.strip(), None
        except subprocess.CalledProcessError as err:
            if attempt < retries - 1:
                time.sleep(delay)  # Wait before retrying
            else:
                return None, f"Command '{command}' failed after {retries} attempts: {err.stderr.strip()}"
    return None, "Unknown error"


def patch_network(network_type, egress_ip, egress_firewall, multicast):
    """Patch the Network.operator.openshift.io cluster resource with generic networkType."""

    # Validate network type
    if network_type not in ["OVNKubernetes", "OpenShiftSDN"]:
        return None, f"Invalid networkType '{network_type}'. Supported: 'OVNKubernetes', 'OpenShiftSDN'."

    # Check if any field is set (prevent empty patch)
    if egress_ip is None and egress_firewall is None and multicast is None:
        return None, "No values provided. Automatic migration will be applied."

    patch_data = {
        "spec": {
            "migration": {
                "networkType": network_type,
                "features": {}
            }
        }
    }

    if egress_ip is not None:
        patch_data["spec"]["migration"]["features"]["egressIP"] = egress_ip
    if egress_firewall is not None:
        patch_data["spec"]["migration"]["features"]["egressFirewall"] = egress_firewall
    if multicast is not None:
        patch_data["spec"]["migration"]["features"]["multicast"] = multicast

    patch_command = f"oc patch Network.operator.openshift.io cluster --type='merge' --patch '{json.dumps(patch_data)}'"
    output, error = run_command_with_retries(patch_command, retries=3, delay=5)
    if error:
        return None, error
    return output, None


def main():
    module = AnsibleModule(
        argument_spec={
            "network_type": {"type": "str", "choices": ["OVNKubernetes", "OpenShiftSDN"], "required": True},  # Takes OpenShiftSDN or OVNKubernetes
            "egress_ip": {"type": "bool", "default": None},
            "egress_firewall": {"type": "bool", "default": None},
            "multicast": {"type": "bool", "default": None}
        },
        supports_check_mode=True,
    )

    network_type = module.params["network_type"]
    egress_ip = module.params["egress_ip"]
    egress_firewall = module.params["egress_firewall"]
    multicast = module.params["multicast"]

    # Patch the network operator
    output, error = patch_network(network_type, egress_ip, egress_firewall, multicast)
    if error:
        module.exit_json(changed=False, msg=error)

    module.exit_json(changed=True, msg=f"Network operator migration settings updated for {network_type}.", output=output)


if __name__ == "__main__":
    main()
