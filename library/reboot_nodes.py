#!/usr/bin/python

from ansible.module_utils.basic import AnsibleModule
import subprocess
import time


def run_command_with_retries(command, retries=3, delay=3):
    """Execute a shell command with retries on failure."""
    for attempt in range(retries):
        try:
            result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
            return result.stdout.strip(), None
        except subprocess.CalledProcessError as e:
            if attempt < retries - 1:
                time.sleep(delay)
            else:
                return None, f"Command failed after {retries} attempts: {e.stderr.strip()}"
    return None, "Unknown error"


def get_nodes(role, retries, delay):
    """Retrieve a list of nodes by role (master/worker)."""
    # command = f"oc get nodes -o custom-columns=NAME:.metadata.name -l node-role.kubernetes.io/{role} | grep -v ROLE | awk '{{print $1}}'"
    command = f"oc get nodes -o custom-columns=NAME:.metadata.name -l node-role.kubernetes.io/{role} --no-headers"
    stdout, error = run_command_with_retries(command, retries, delay)
    if error:
        return None, error
    return stdout.splitlines(), None


def get_pod_on_node(node, namespace, daemonset_label, retries, delay):
    """Retrieve the pod name on a specific node."""
    command = (
        f"oc get pods -n {namespace} -o custom-columns=NAME:.metadata.name,NODE:.spec.nodeName "
        f"| grep {node} | grep {daemonset_label} | awk '{{print $1}}'"
    )
    stdout, error = run_command_with_retries(command, retries, delay)
    if error:
        return None, error
    return stdout.strip(), None


def reboot_node(pod, namespace, delay, retries):
    """Reboot a node by executing a reboot command on its pod."""
    command = f"oc rsh -n {namespace} {pod} chroot /rootfs shutdown -r +{delay}"
    stdout, error = run_command_with_retries(command, retries, delay)
    return stdout, error


def wait_for_nodes_unreachable(delay):
    """Wait for the API server to become unreachable after node reboots."""
    time.sleep(delay * 60)  # Wait for the specified delay in minutes


def wait_for_nodes_ready(timeout, retries, delay):
    """Wait for all nodes to become ready within a timeout."""
    start_time = time.time()
    while time.time() - start_time < timeout:
        command = "oc wait node --all --for condition=ready --timeout=60s"
        stdout, error = run_command_with_retries(command, retries, delay)
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
    nodes, error = get_nodes(role, retries, retry_delay)
    if error:
        module.fail_json(msg=f"Failed to get {role} nodes: {error}")

    # Step 2: Reboot nodes sequentially
    reboot_results = []
    for node in nodes:
        pod, error = get_pod_on_node(node, namespace, daemonset_label, retries, retry_delay)
        if error:
            module.fail_json(msg=f"Failed to get pod for node {node}: {error}")

        stdout, error = reboot_node(pod, namespace, delay, retries)
        if error:
            reboot_results.append({"node": node, "status": "failed", "error": error})
            module.fail_json(msg=f"failed to reboot node {node} due to error: {error}")
        else:
            reboot_results.append({"node": node, "status": "success", "output": stdout})
        delay += 3  # Increment delay for subsequent nodes

    # Step 3: Wait for API server to become unreachable
    wait_for_nodes_unreachable(delay)

    # Step 4: Wait for all nodes to become ready
    if not wait_for_nodes_ready(timeout, retries, retry_delay):
        module.fail_json(msg="Nodes did not become ready within the timeout period.")

    module.exit_json(changed=True, results=reboot_results, msg="All nodes rebooted and ready.")


if __name__ == "__main__":
    main()
