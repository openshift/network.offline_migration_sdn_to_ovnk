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

- Make sure `jq` is installed in your system.

### Using the playbooks:

- Clone the repository as follows:
```shell
git clone git@github.com:openshift/network.offline_migration_sdn_to_ovnk.git
```

- Change to that directory:
``` shell
cd network.offline_migration_sdn_to_ovnk
```

- Build the ansible collection:
```shell
ansible-galaxy collection build .
```

- Install the ansible collection:
```shell
ansible-galaxy collection install  network-offline_migration_sdn_to_ovnk-1.0.0.tar.gz
```

-  Check if the collection is installed:
```shell
ansible-galaxy collection list | grep network.offline_migration_sdn_to_ovnk 
```

- To run the migration from OpenShiftSDN to OVNKubernetes
```shell
ansible-playbook -v playbook-migration.yml
```

- To run the rollback from OVNKubernetes to OpenShiftSDN
```shell
ansible-playbook -v playbook-rollback.yml
```

- Disable auto-migration features

In `migration-playbook.yml` or `rollback-playbook.yml` based on whether you are migrating or rollback
please set the following:

To disable auto-migration of features:
```shell
        disable_auto_migration: true # true enables disable_automatic_migration. You will need to set egress_ip, egress_firewall and multicast as follows:
        egress_ip: false
        egress_firewall: false
        multicast: false
```

To keep automigration enabled:
```shell
        disable_auto_migration: false
```

- Customize network features:
  - In `migration-playbook.yml` you can set the following fields with custom values:
```shell
        mtu: 1400
        geneve_port: 6081
        ipv4_subnet: "100.64.0.0/16"
```
  - In the rollback-playbook.yml you can set the following fields with custom values:
```shell
        mtu: 1400
        vxlanPort: 4790
```
