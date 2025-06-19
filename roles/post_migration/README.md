# `post_migration` role

Part of the **network.offline_migration_sdn_to_ovnk** collection.

# `post_migration` role  
*Part of the `network.offline_migration_sdn_to_ovnk` collection*

Performs the **post-flight validation, clean-up** tasks
after an OpenShift cluster has switched its default network from
**OpenShiftSDN** to **OVNKubernetes**.

Typical responsibilities include:

- Check all cluster operators back to normal.
- Check the CNI network provider.
- Check if all cluster nodes are in Ready state.
- Notify user about NotReady nodes.
- Confirm that no pods are in an error state.
- Notify user if any pods are in an error state.
- Patch Network.operator.openshift.io and wait for migration field to clear.
- Remove network configuration and namespace.
- Check all cluster operators back to normal.

---

## Requirements

| Item                            | Notes |
|---------------------------------|-------|
| **OpenShift 4.12+ and <=4.16**  | Cluster admin privileges (`oc` logged in as a user with `cluster-admin`). |
| **`oc` CLI in `$PATH`**         | Used by many tasks via `ansible.builtin.command`. |
| **Ansible >= 2.18**             | Collection relies on modern plugins & loop syntax. |
| **Python 3.12+ on control host** | Needed for the `openshift` Python client when running sanity checks. |

---

## Role variables

| Variable | Default | Description                                                                 |
|----------|--|-----------------------------------------------------------------------------|
| `post_migration_checks` |  |  Adds list of conditions to wait until the desired status is achieved.                   |
| `post_migration_expected_network_type` |  | Check if CNI `OVNKubernetes` was set after migration.                       |
| `post_migration_network_provider_config` |  | Checks if custom network configuration for `openshiftSDNConfig` is deleted. |
| `post_migration_namespace` |  | Checks if namespace `openshift-sdn` is deleted after migration.             |

> **Tip** – override only what you need; place customised variables in a
> host-vars file or pass them at runtime with `-e`.

---

## Dependencies

* No external roles.

---

## Example playbook

```yaml
---
- name: Post Migration
  hosts: localhost
  gather_facts: false
  roles:
    - role: network.offline_migration_sdn_to_ovnk.post_migration
      vars:
        post_migration_checks:
          - "oc wait co --all --for='condition=Available=True' --timeout=60s"
          - "oc wait co --all --for='condition=Progressing=False' --timeout=60s"
          - "oc wait co --all --for='condition=Degraded=False' --timeout=60s"
        post_migration_expected_network_type: OVNKubernetes
        post_migration_network_provider_config: openshiftSDNConfig
        post_migration_namespace: openshift-sdn
        post_migration_clean_migration_timeout: 120
```

## License

Apache-2.0

## Authors

@miheer