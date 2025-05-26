# Copyright (c) 2025, Red Hat
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)


DOCUMENTATION = r"""
---
module: check_nodes_ready
short_description: Check if all cluster nodes are in Ready state.
version_added: "1.0.0"
author: Miheer Salunke (@miheer)
description:
  - Check if all cluster nodes are in Ready state.
options:
  timeout:
    description: Timeout in seconds.
    type: int
    default: 120
"""
EXAMPLES = r"""
- name: Check if all cluster nodes are in Ready state
  network.offline_migration_sdn_to_ovnk.check_nodes_ready:
  register: node_status

- name: Notify user about NotReady nodes
  ansible.builtin.debug:
    msg: >
      The following nodes are not in the Ready state:  {{ node_status.not_ready_nodes | map(attribute='name') | join(', ') }}.
      Please investigate machine config daemon pod logs.

  when: node_status.not_ready_nodes | length > 0
"""
RETURN = r"""
changed:
  description: Whether the CR was modified.
  type: bool
  returned: always
"""

from ansible.module_utils.basic import AnsibleModule
import json
import time


def run_command(module, command):
    """Run a shell command safely using module.run_command and return output or raise an error."""
    rc, stdout, stderr = module.run_command(command)

    if rc == 0:
        return stdout.strip(), None  # Success

    return None, f"Command '{' '.join(command)}' failed: {stderr.strip()}"


def get_nodes(module, timeout):
    """Fetch the nodes and their status."""
    command = "oc get nodes -o json"
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            output, error = run_command(module, command)
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
                msg=(
                    "Some nodes are not in the Ready state. Please investigate the "
                    "Machine Config Daemon pod logs with:\n"
                    "`oc get pod -n openshift-machine-config-operator`\n"
                    "and resolve any errors."
                ),
                not_ready_nodes=not_ready_nodes,
            )
        module.exit_json(changed=False, msg="All nodes are in the Ready state.", not_ready_nodes=not_ready_nodes)
    except Exception as e:
        module.fail_json(msg=str(e))


if __name__ == "__main__":
    main()
