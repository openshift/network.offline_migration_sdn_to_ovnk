#!/usr/bin/python

from ansible.module_utils.basic import AnsibleModule
import os


def main():
    module = AnsibleModule(argument_spec={})
    kubeconfig_path = os.environ.get("KUBECONFIG")
    if not kubeconfig_path:
        module.fail_json(
            msg="The KUBECONFIG environment variable is not set."
        )

    if not os.path.isfile(kubeconfig_path):
        module.fail_json(
            msg=f"The KUBECONFIG file does not exist at the specified path: {kubeconfig_path}.",
            kubeconfig_path=kubeconfig_path
        )

    module.exit_json(
        changed=False,
        msg=f"KUBECONFIG is set, and the file exists at: {kubeconfig_path}.",
        kubeconfig_path=kubeconfig_path
    )


if __name__ == "__main__":
    main()
