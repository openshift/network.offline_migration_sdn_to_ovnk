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


def get_nodes(module, timeout):
    """Fetch the nodes and their status."""
    command = "oc get nodes -o json"
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            output, error = run_command(command)
            if not error:
                nodes = json.loads(output).get("items", [])
            elif error:
                module.warn(f"Retrying as got an error: {error}")
            time.sleep(3)
        except Exception as ex:
            module.fail_json(msg=str(ex))
    node_status = []
    for node in nodes:
        name = node.get("metadata", {}).get("name")
        conditions = node.get("status", {}).get("conditions", [])
        ready_condition = next((c for c in conditions if c.get("type") == "Ready"), {})
        status = ready_condition.get("status", "Unknown")
        node_status.append({"name": name, "status": status})
    return node_status


def main():
    module_args = dict(
        timeout=dict(type="int", default=120),  # Timeout in seconds
    )
    module = AnsibleModule(argument_spec=module_args, supports_check_mode=True)
    timeout = module.params["timeout"]
    try:
        nodes = get_nodes(module, timeout)
        not_ready_nodes = [n for n in nodes if n["status"] != "True"]
        if not_ready_nodes:
            module.exit_json(
                changed=False,
                msg="Some nodes are not in the Ready state. Please investigate the machine config daemon pod logs using the command `oc get pod -n openshift-machine-config-operator` and resolve any errors.",
                not_ready_nodes=not_ready_nodes,
            )
        module.exit_json(changed=False, msg="All nodes are in the Ready state.", not_ready_nodes=not_ready_nodes)
    except Exception as e:
        module.fail_json(msg=str(e))


if __name__ == "__main__":
    main()
