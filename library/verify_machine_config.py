#!/usr/bin/python

from ansible.module_utils.basic import AnsibleModule
import re
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


def get_machine_config_status(timeout):
    start_time = time.time()
    while time.time() - start_time < timeout:
        output, error = run_command("oc describe node | egrep 'hostname|machineconfig'")
        if not error:
            nodes = re.findall(
                r"kubernetes\.io/hostname=(?P<hostname>.+)\n.*currentConfig: (?P<currentConfig>.+)\n.*desiredConfig: (?P<desiredConfig>.+)\n.*state: (?P<state>.+)",
                output,
                re.MULTILINE,
            )
        time.sleep(10)  # Check every 10 seconds
    return nodes


def verify_machine_config(module, config_name, network_type):
    start_time = time.time()
    while time.time() - start_time < module.params["timeout"]:
        try:
            output, error = run_command(f"oc get machineconfig {config_name} -o yaml | grep ExecStart")
            if not error:
                if network_type == "OVNKubernetes":
                    if "ExecStart=/usr/local/bin/configure-ovs.sh OVNKubernetes" in output:
                        return True
                if network_type == "OpenShiftSDN":
                    if "ExecStart=/usr/local/bin/configure-ovs.sh OpenShiftSDN" in output:
                        return True
            if error:
                module.warn(f"Retrying as got an error: {error}")
            time.sleep(3)
        except Exception as ex:
            module.fail_json(msg=str(ex))

    return False


def main():
    module = AnsibleModule(
        argument_spec=dict(
            timeout=dict(type="int", default=300),
            network_type=dict(type="str", required=True),
        )
    )
    timeout = module.params["timeout"]
    network_type = module.params["network_type"]
    try:
        nodes = get_machine_config_status(timeout)
        issues = []
        for node in nodes:
            if node["state"] != "Done":
                issues.append(f"Node {node['hostname']} state is {node['state']}, not Done.")
            if node["currentConfig"] != node["desiredConfig"]:
                issues.append(
                    f"Node {node['hostname']} currentConfig ({node['currentConfig']}) does not match desiredConfig ({node['desiredConfig']})."
                )
            if not verify_machine_config(module, node["currentConfig"], network_type):
                issues.append(
                    f"Node {node['hostname']} configuration {node['currentConfig']} does not contain expected ExecStart."
                )
        if issues:
            module.fail_json(msg="Issues detected with machine configuration.", issues=issues)

        module.exit_json(changed=False, msg="All machine configurations are correct.", issues=[])
    except Exception as e:
        module.fail_json(msg=str(e))


if __name__ == "__main__":
    main()
