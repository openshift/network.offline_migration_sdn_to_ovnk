## Migration from OpenShiftSDN to OVNKubernetes and Rollback from OVNKubernetes to OpenShiftSDN

### Pre-requisites

- Python latest package installed from https://www.python.org/.
  This has been tested with [installer](https://www.python.org/downloads/release/python-3131/)
- After installation of python install ansible using the following command:
  ```shell
  python3 -m pip install --user ansible
  ```
  Reference: [Installing Ansible](https://docs.ansible.com/ansible/latest/installation_guide/intro_installation.html#pip-install)
- For running tests install the following:
```shell
  python3 -m pip install --user jmespath
```

### Using the playbooks:

- Clone the repository as follows:
```shell
git clone git@github.com:miheer/ansible-sdn-to-ovn-migration.git
```

- Change to that directory:
```
cd ansible-sdn-to-ovn-migration.git
```

- To run the migration from OpenShiftSDN to OVNKubernetes
```shell
ansible-playbook -v playbook-migration.yml
```

- To run the rollback from OVNKubernetes to OpenShiftSDN
```shell
ansible-playbook -v playbook-rollback.yml
```