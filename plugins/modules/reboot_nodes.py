#!/usr/bin/python

# Copyright (c) 2025, Red Hat
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)


DOCUMENTATION = r"""
---
module: reboot_nodes
short_description: Change the default network type (SDN ↔ OVN).
version_added: "1.0.0"
author: Miheer Salunke (@miheer)
description:
  - Switches the cluster DefaultNetwork between C(OpenShiftSDN)
    and C(OVNKubernetes) by patching the Network.operator CR.
options:
  new_type:
    description: Desired network type.
    choices: [OpenShiftSDN, OVNKubernetes]
    required: true
"""
EXAMPLES = r"""
- name: Migrate to OVN-K
  network.offline_migration_sdn_to_ovnk.change_network_type:
    new_type: OVNKubernetes
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
    """Execute a shell command safely using module.run_command with retries."""
    for attempt in range(retries):
        rc, stdout, stderr = module.run_command(command)

        if rc == 0:
            return stdout.strip(), None  # ✅ Success

        if attempt < retries - 1:
            module.warn(f"Retrying in {delay} seconds due to error: {stderr.strip()}")
            time.sleep(delay)  # Wait before retrying
        else:
            return None, f"❌ Command failed after {retries} attempts: {stderr.strip()}"

    return None, "❌ Unknown error"


def get_nodes(module, role, retries, delay):
    """Retrieve a list of nodes by role."""
    command = ["oc", "get", "nodes", "-o", "json"]
    stdout, error = run_command_with_retries(module, command, retries, delay)
    if error:
        return None, error

    try:
        nodes_json = json.loads(stdout)
        nodes = []
        for item in nodes_json.get("items", []):
            labels = item.get("metadata", {}).get("labels", {})
            node_name = item.get("metadata", {}).get("name")

            if role == "master":
                if "node-role.kubernetes.io/master" in labels:
                    nodes.append(node_name)
            else:
                if "node-role.kubernetes.io/master" not in labels:
                    nodes.append(node_name)

        if not nodes:
            return None, "❌ No nodes found for the specified role."
        return nodes, None

    except json.JSONDecodeError:
        return None, "❌ Failed to parse JSON output from `oc get nodes`."


def get_pod_on_node(module, node, namespace, daemonset_label, retries, delay):
    """Retrieve the pod running on a specific node."""
    command = ["oc", "get", "pods", "-n", namespace, "-o", "json"]
    stdout, error = run_command_with_retries(module, command, retries, delay)
    if error:
        return None, error

    try:
        pods_json = json.loads(stdout)
        for pod in pods_json.get("items", []):
            pod_name = pod.get("metadata", {}).get("name")
            pod_node = pod.get("spec", {}).get("nodeName")
            labels = pod.get("metadata", {}).get("labels", {})

            if pod_node == node and daemonset_label in labels.values():
                return pod_name, None

        return None, f"❌ No matching pod found on node {node} for label {daemonset_label}."

    except json.JSONDecodeError:
        return None, "❌ Failed to parse JSON output from `oc get pods`."


def reboot_node(module, pod, namespace, delay, retries):
    """Reboot a node using `oc rsh` into the MCD pod."""
    command = ["oc", "rsh", "-n", namespace, pod, "chroot", "/rootfs", "shutdown", "-r", f"+{delay}"]
    stdout, error = run_command_with_retries(module, command, retries, delay)
    return stdout, error


def wait_for_nodes_unreachable(delay):
    """Wait for nodes to reboot by sleeping for the specified delay in minutes."""
    time.sleep(delay * 60)  # ⏳ Wait for reboot to take effect


def wait_for_nodes_ready(module, timeout, retries, delay):
    """Wait for all nodes to become ready within a timeout."""
    start_time = time.time()
    while time.time() - start_time < timeout:
        command = ["oc", "wait", "node", "--all", "--for", "condition=ready", "--timeout=60s"]
        stdout, error = run_command_with_retries(module, command, retries, delay)
        if not error:
            return True
        time.sleep(10)
    return False


def main():
    module_args = dict(
        role=dict(type="str", required=True, choices=["master", "worker"]),
        namespace=dict(type="str", required=True),
        daemonset_label=dict(type="str", required=True),
        delay=dict(type="int", default=1),
        retries=dict(type="int", default=3),
        retry_delay=dict(type="int", default=3),
        timeout=dict(type="int", default=1800),  # Default timeout for nodes to come back
    )

    module = AnsibleModule(argument_spec=module_args, supports_check_mode=True)

    role = module.params["role"]
    namespace = module.params["namespace"]
    daemonset_label = module.params["daemonset_label"]
    delay = module.params["delay"]
    retries = module.params["retries"]
    retry_delay = module.params["retry_delay"]
    timeout = module.params["timeout"]

    # Step 1: Get nodes of the specified role
    nodes, error = get_nodes(module, role, retries, retry_delay)
    if error:
        module.fail_json(msg=f"❌ Failed to get {role} nodes: {error}")

    # Step 2: Reboot nodes sequentially
    reboot_results = []
    for node in nodes:
        pod, error = get_pod_on_node(module, node, namespace, daemonset_label, retries, retry_delay)
        if error:
            module.fail_json(msg=f"❌ Failed to get pod for node {node}: {error}")

        stdout, error = reboot_node(module, pod, namespace, delay, retries)
        if error:
            reboot_results.append({"node": node, "status": "failed", "error": error})
            module.fail_json(msg=f"❌ Failed to reboot node {node} due to error: {error}")
        else:
            reboot_results.append({"node": node, "status": "success", "output": stdout})

        delay += 3  # 🔄 Increment delay for subsequent nodes

    # Step 3: Wait for API server to become reachable
    wait_for_nodes_unreachable(delay)

    # Step 4: Wait for all nodes to become ready
    if not wait_for_nodes_ready(module, timeout, retries, retry_delay):
        module.fail_json(msg="❌ Nodes did not become ready within the timeout period.")

    module.exit_json(changed=True, results=reboot_results, msg="✅ All nodes rebooted and ready.")


if __name__ == "__main__":
    main()
