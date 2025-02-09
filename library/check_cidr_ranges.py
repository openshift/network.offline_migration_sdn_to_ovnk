from ansible.module_utils.basic import AnsibleModule
import ipaddress
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


def get_used_cidrs(module, timeout):
    """Retrieve all CIDR ranges currently in use on the cluster."""
    command = "oc get network.config/cluster -o json"
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
    networks = []
    if output:
        network_config = json.loads(output)
        # Check clusterNetwork
        cluster_networks = network_config.get("spec", {}).get("clusterNetwork", [])
        for network in cluster_networks:
            networks.append(network.get("cidr"))
        # Check serviceNetwork
        service_networks = network_config.get("spec", {}).get("serviceNetwork", [])
        networks.extend(service_networks)
        # Check machineNetwork
        machine_networks = network_config.get("status", {}).get("networking", {}).get("machineNetwork", [])
        for network in machine_networks:
            networks.append(network.get("cidr"))
    return networks


def check_cidr_ranges(conflicting_ranges, used_ranges):
    """Check if any conflicting CIDRs are in use."""
    conflicting_cidrs = []
    for conflicting_range in conflicting_ranges:
        conflict_network = ipaddress.ip_network(conflicting_range)
        for used_range in used_ranges:
            used_network = ipaddress.ip_network(used_range)
            if conflict_network.overlaps(used_network):
                conflicting_cidrs.append(conflicting_range)
    return conflicting_cidrs


def main():
    module = AnsibleModule(
        argument_spec={
            "conflicting_ranges": {"type": "list", "elements": "str", "required": True},
            "timeout": {"type": "int", "default": 120},  # Timeout in seconds
        },
        supports_check_mode=True,
    )

    conflicting_ranges = module.params["conflicting_ranges"]
    timeout = module.params["timeout"]

    try:
        used_cidrs = get_used_cidrs(module, timeout)
        conflicting_cidrs = check_cidr_ranges(conflicting_ranges, used_cidrs)
        if conflicting_cidrs:
            module.fail_json(
                msg=f"Conflicting CIDR ranges found: {', '.join(conflicting_cidrs)}",
                conflicting_cidrs=conflicting_cidrs,
                used_cidrs=used_cidrs,
            )
        else:
            module.exit_json(
                changed=False,
                msg="No conflicting CIDR ranges found.",
                used_cidrs=used_cidrs,
            )
    except Exception as e:
        module.fail_json(msg=str(e))


if __name__ == "__main__":
    main()
