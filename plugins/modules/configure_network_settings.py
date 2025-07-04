# Copyright (c) 2025, Red Hat
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)


DOCUMENTATION = r"""
---
module: configure_network_settings
short_description: Configure MTU, tunnel ports, internal subnet and gateway settings.
version_added: "1.0.0"
author: Miheer Salunke (@miheer)
description:
  - Patch the C(Network.operator.openshift.io/cluster) custom resource either
    while migrating to OVN-Kubernetes or rolling back to OpenShift SDN.
  - For migration (OVN-Kubernetes)* you may adjust
    C(mtu), C(geneve_port), C(ipv4_subnet) or any combination of them.
  - For rollback (OpenShiftSDN)* you may adjust C(vxlanPort) and/or C(mtu).
  - Gateway options C(routing_via_host) and C(ip_forwarding) are honoured
    **only** when C(configure_network_type=ovnKubernetes).
options:
  configure_network_type:
    description: Which default network plugin you want to patch.
    choices: [ovnKubernetes, openshiftSDN]
    required: true
    type: str
  mtu:
    description: Desired MTU to configure on the overlay network.
    type: int
    required: false
  geneve_port:
    description: Geneve UDP destination port to use (OVN-Kubernetes only).
    type: int
    required: false
  ipv4_subnet:
    description: Internal IPv4 subnet (CIDR) for OVN-Kubernetes.  Ignored for SDN.
    type: str
    required: false
  retries:
    description: Defined the number of retries for oc command incase of a failure.
    type: int
    default: 3
  delay:
    description: Defines the delay between retries.
    type: int
    default: 5
  vxlanPort:
    description: Provide the vxlanPort
    type: int
    required: false
  routing_via_host:
    description:
      - When set to C(true) the node operates in *local-gateway* mode and all
        pod egress is first routed through the host network stack.
      - When C(false) (default) the node stays in *shared-gateway* mode.
      - Applicable only when C(configure_network_type=ovnKubernetes).
    type: bool
  ip_forwarding:
    description:
      - Set to C(Global) if the host network should forward IP traffic that is
        unrelated to OVN-Kubernetes; use C(Restricted) (default) to turn that
        off.
      - Applicable only together with local-gateway mode
        (see C(routing_via_host)).
    type: str
    choices: [Global, Restricted]
"""
EXAMPLES = r"""
- name: Customize network settings if parameters are provided
  network.offline_migration_sdn_to_ovnk.configure_network_settings:
    configure_network_type: "{{ rollback_configure_network_type }}"
    mtu: "{{ rollback_mtu | default(omit) }}"
    vxlanPort: "{{ rollback_vxlanPort | default(omit) }}"
    retries: 3
    delay: 5
  register: patch_result
- name: Customize network settings if parameters are provided
  network.offline_migration_sdn_to_ovnk.configure_network_settings:
    configure_network_type: "{{ migration_configure_network_type }}"
    mtu: "{{ migration_mtu | default(omit) }}"
    geneve_port: "{{ migration_geneve_port | default(omit) }}"
    ipv4_subnet: "{{ migration_ipv4_subnet | default(omit) }}"
    retries: 3
    delay: 5
  register: patch_result
"""
RETURN = r"""
changed:
  description: Whether the CR was modified.
  type: bool
  returned: always
"""

from ansible.module_utils.basic import AnsibleModule
import time
import json


def run_command_with_retries(module, command, retries=3, delay=3):
    """Execute a shell command with retries on failure."""
    for attempt in range(retries):
        rc, stdout, stderr = module.run_command(command)

        if rc == 0:
            return stdout.strip(), None  # Success

        if attempt < retries - 1:
            module.warn(f"Retrying in {delay} seconds due to error: {stderr.strip()}")
            time.sleep(delay)  # Wait before retrying
        else:
            return None, f"Command failed after {retries} attempts: {stderr.strip()}"

    return None, "Unknown error"


def run_patch_command(module, patch_command, retries, delay):
    """Execute the oc patch command with retries."""
    if module.check_mode:
        module.exit_json(changed=True, msg="Check mode: Patch command prepared", command=patch_command)

    try:
        output, error = run_command_with_retries(module, patch_command, retries=retries, delay=delay)
        if not error:
            module.exit_json(changed=True, msg="Network configuration patched successfully.", output=output)
        else:
            module.fail_json(msg=f"Patch command failed: {error}")
    except Exception as e:
        module.fail_json(msg=f"Unexpected error while executing patch command: {str(e)}")


def main():
    module = AnsibleModule(
        argument_spec={
            "configure_network_type": {"type": "str", "choices": ["ovnKubernetes", "openshiftSDN"], "required": True},
            "mtu": {"type": "int", "required": False},
            "geneve_port": {"type": "int", "required": False},
            "ipv4_subnet": {"type": "str", "required": False},
            "retries": {"type": "int", "default": 3},
            "delay": {"type": "int", "default": 5},
            "vxlanPort": {"type": "int", "required": False},
            "routing_via_host": {"type": "bool", "required": False},
            "ip_forwarding": {"type": "str", "choices": ["Global", "Restricted"], "required": False}
        },
        supports_check_mode=True,
    )

    network_type = module.params["configure_network_type"]
    mtu = module.params["mtu"]
    geneve_port = module.params["geneve_port"]
    ipv4_subnet = module.params["ipv4_subnet"]
    retries = module.params["retries"]
    delay = module.params["delay"]
    vxlanPort = module.params["vxlanPort"]
    routing_via_host = module.params["routing_via_host"]
    ip_forwarding = module.params["ip_forwarding"]

    # Ensure patching is needed
    if not any([mtu, geneve_port, ipv4_subnet, vxlanPort, routing_via_host, ip_forwarding]):
        module.exit_json(changed=False, msg="No changes required. No valid parameters provided.")

    # Build the patch payload
    if routing_via_host or ip_forwarding:
        patch_data = {"spec": {"defaultNetwork": {f"{network_type}Config": {"gatewayConfig": {}}}}}
    else:
        patch_data = {"spec": {"defaultNetwork": {f"{network_type}Config": {}}}}

    if network_type == "ovnKubernetes":
        if mtu:
            patch_data["spec"]["defaultNetwork"][f"{network_type}Config"]["mtu"] = mtu
        if geneve_port:
            patch_data["spec"]["defaultNetwork"][f"{network_type}Config"]["genevePort"] = geneve_port
        if ipv4_subnet:
            patch_data["spec"]["defaultNetwork"][f"{network_type}Config"]["v4InternalSubnet"] = ipv4_subnet
        if vxlanPort:
            module.warn("vxlanPort can't be set in ovnKubernetesConfig")
        if routing_via_host:
            patch_data["spec"]["defaultNetwork"][f"{network_type}Config"]["gatewayConfig"]["routingViaHost"] = routing_via_host
        if ip_forwarding:
            patch_data["spec"]["defaultNetwork"][f"{network_type}Config"]["gatewayConfig"]["ipForwarding"] = ip_forwarding

        # Prepare and execute patch command
        patch_command = f"oc patch Network.operator.openshift.io cluster --type=merge --patch '{json.dumps(patch_data)}'"
        run_patch_command(module, patch_command, retries, delay)

    elif network_type == "openshiftSDN":
        if mtu:
            patch_data["spec"]["defaultNetwork"][f"{network_type}Config"]["mtu"] = mtu
        if vxlanPort:
            patch_data["spec"]["defaultNetwork"][f"{network_type}Config"]["vxlanPort"] = vxlanPort
        if geneve_port or ipv4_subnet:
            module.warn("geneve_port or ipv4_subnet can't be set in openshiftSDNConfig")
        # Prepare and execute patch command
        patch_command = f"oc patch Network.operator.openshift.io cluster --type=merge --patch '{json.dumps(patch_data)}'"
        run_patch_command(module, patch_command, retries, delay)

    else:
        module.exit_json(changed=False, msg="No changes patched. No valid parameters provided.")


if __name__ == "__main__":
    main()
