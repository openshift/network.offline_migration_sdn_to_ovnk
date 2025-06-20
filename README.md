## Migration from OpenShiftSDN to OVNKubernetes and Rollback from OVNKubernetes to OpenShiftSDN

### Note: This repository is under development and not recommended to use on production environment and is not supported by Red Hat.

### Pre-requisites

#### Ensure system is updated before installation
- If you are on RHEL9:
```shell
yum clean all && yum update -y
dnf -y upgrade --refresh && dnf clean all
```

#### Install necessary dependencies
```shell
dnf install -y \
      glibc-langpack-en \
      git \
      make \
      python3.12 \
      python3.12-pip \
      gcc \
      jq  

python3.12 -m pip install --no-cache-dir --upgrade pip \
python3.12 -m pip install --no-cache-dir ansible-core==2.18.1 \
python3.12 -m pip install --no-cache-dir ansible-lint==25.4.0 \
python3.12 -m pip install --no-cache-dir  jmespath \
rm -rf /var/cache/dnf
```

- Minimum of python 3.12, ansible-core 2.18.1 and ansible-lint 25.4.0 is recommended.

#### Alternative way:

- Python latest package installed from https://www.python.org/.
  This has been tested with [installer](https://www.python.org/downloads/release/python-3131/)

- After installation of python install ansible using the following command:
  ```shell
  python3 -m pip install --user ansible  # Make sure ansible version is 2.18.1
  ```
  Reference: [Installing Ansible](https://docs.ansible.com/ansible/latest/installation_guide/intro_installation.html#pip-install)

- For running tests install the following:
```shell
  python3 -m pip install --user jmespath
```

- Make sure `jq` is installed in your system.

- You can install the packages mentioned in section [Install necessary dependencies](#install-necessary-dependencies)
  as per your requirements.

### Using the playbooks:

- Clone the repository as follows:
```shell
git clone git@github.com:openshift/network.offline_migration_sdn_to_ovnk.git
```

- Change to that directory:
``` shell
cd network.offline_migration_sdn_to_ovnk
```

- Install the ansible collection:
```shell
make install
```

-  Check if the collection is installed:
```shell
ansible-galaxy collection list | grep network.offline_migration_sdn_to_ovnk 
```

- To run the migration from OpenShiftSDN to OVNKubernetes
```shell
ansible-playbook -v playbooks/playbook-migration.yml
```

- To run the rollback from OVNKubernetes to OpenShiftSDN
```shell
ansible-playbook -v playbooks/playbook-rollback.yml
```

- Disable auto-migration features

In `migration-playbook.yml` or `rollback-playbook.yml` based on whether you are migrating or rollback
please set the following:

To disable auto-migration of features:
```shell
        migration_disable_auto_migration: true # true enables disable_automatic_migration. You will need to set egress_ip, egress_firewall and multicast as follows:
        migration_egress_ip: false
        migration_egress_firewall: false
        migration_multicast: false
```

To keep automigration enabled:
```shell
        migration_disable_auto_migration: false
```

If you are setting under rollback playbook you need to add prefix `rollback_` to the mentioned vars above instead
of `migration_`

- Customize network features:
  - In `migration-playbook.yml` you can set the following fields with custom values:
```shell
        migration_mtu: 1400
        migration_geneve_port: 6081
        migration_ipv4_subnet: "100.64.0.0/16"
```
  - In the rollback-playbook.yml you can set the following fields with custom values:
```shell
        rollback_mtu: 1400
        rollback_vxlanPort: 4790
```

If you are setting under rollback playbook you need to add prefix `rollback_` to the mentioned vars above instead
of `migration_`


- If you use nncp on primary interface then during migration pass the primary interface name in the playbook `playbooks/migration-playbook.yml`:
```shell
migration_interface_name: eth0
```

### Testing

- You must run lint tests after making any changes to the code.
```shell
make lint
```

- You must run sanity tests after making any changes to the code.
```shell
make sanity
```

- You must run galaxy import test after making any changes to the code.
```shell
make import
```

- To check how things work in CI:

Assuming if you have access to registry.ci.openshift.org.
- docker login:
```shell
cat hack/docker-login.sh 
#!/usr/bin/env bash

PULL_SECRET="pull-secret.json"
REGISTRY="registry.ci.openshift.org"
USERNAME=$(jq -r ".auths[\"$REGISTRY\"].auth" < "$PULL_SECRET" | base64 -d | cut -d: -f1)
PASSWORD=$(jq -r ".auths[\"$REGISTRY\"].auth" < "$PULL_SECRET" | base64 -d | cut -d: -f2)
echo "$PASSWORD" | docker login "$REGISTRY" -u "$USERNAME" --password-stdin
```

- docker build:
```shell
docker build --file ci/Dockerfile --tag quay.io/<your reponame>/ansible-test-runner:1 .
```

- docker push:
```
docker push quay.io/<your reponame>/ansible-test-runner:1
```

- Run the job in your OpenShift Environment:
```shell
ANSIBLE_TEST_IMAGE=quay.io/<your reponame>/ansible-test-runner:1 ./ci/incluster_intergration.sh
```

- For testing ansible and sanity tests on CI please use scripts `test_incluster_lint.sh` and
  `test_incluster_sanity_lint.sh` respectively

- If you don't have access to registry.ci.openshift.org then you can use Dockerfile.debug to build your image.

### Build and Release

Export the [Ansible Hub Token](https://docs.redhat.com/en/documentation/red_hat_ansible_automation_platform/2.1/html/getting_started_with_automation_hub/proc-create-api-token). 

Make sure you have access to publish the namespace `network`.
You need to go to this namespace link here -> https://console.redhat.com/ansible/automation-hub/namespaces/network/. 
When you load this page you should be able to see a button on the top right of your screen that says 
"upload collection". If you do not see that that means that the account that you are using isn't part
of the RedHat group that is in charge of that namespace.

- Create the fragment:
```bash
mkdir -p changelogs/fragments
cat > changelogs/fragments/1.0.1-bugfixes.yml <<'EOF'
release_summary: |
  Patch release focusing on idempotency and CI hygiene.

bugfixes:
  - Fix undefined variable `migration_interface_name` in the *migration* role (#78).
  - Ensure `verify_cluster_operators_health` waits for operators to settle (#81).

minor_changes:
  - Add `make sanity` target to Makefile.
EOF
```

Valid section keys are major_changes, minor_changes, bugfixes, breaking_changes, security_fixes, deprecated_features,
removed_features, known_issues, plus the optional release_summary block. Reference: docs.ansible.com

Validating [changelog fragments](https://ansible.readthedocs.io/projects/antsibull-changelog/changelogs/#validating-changelog-fragments
):
If you want to do a basic syntax check of changelog fragments, you can run:
```bash
antsibull-changelog lint
```

or run:
```bash
antsibull-changelog lint changelogs/fragments/1.0.1-bugfixes.yml
```

- Bump galaxy.yml (and the VERSION line in the Makefile)
```bash
sed -i -e 's/^version: .*/version: 1.0.1/' galaxy.yml
sed -i -e 's/^VERSION *= *.*/VERSION = 1.0.1/' Makefile
```

Generate the real changelog and finalize the release branch:

When you are ready to publish:
```bash
antsibull-changelog release --version 1.0.1   # rewrites CHANGELOG.rst and changelogs/changelog.yaml
```

Tag and push:
```bash
 git add CHANGELOG.rst Makefile changelogs/changelog.yaml galaxy.yml
 git commit -m "your message"
 git push -f <your remote> <local branch>:<remote branch>
```

Create a PR.

Once the code already is merged:
Tag and push your release to github:
```sh
git push origin HEAD:refs/tags/v1.0.1
````

Rebuild the tarball:
```sh
make build
```
You will get network-offline_migration_sdn_to_ovnk-1.0.1.tar.gz.

Publish:
```sh
export AH_TOKEN=xxxxx 
make publish
```
