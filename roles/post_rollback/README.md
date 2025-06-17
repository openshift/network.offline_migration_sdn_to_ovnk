# `post_rollback` role

Part of the **network.offline_migration_sdn_to_ovnk** collection.

After aborting or rolling back an attempted **OpenShiftSDN → OVNKubernetes**
migration, this role restores cluster settings to a **clean
OpenShiftSDN** state and confirms that all control-plane components are again
healthy.

Key actions:

- Resume MCPs after reboot which were paused during rollback.
- Wait until MCO starts applying new machine config to nodes.
- Check all cluster operators back to normal.
- Verify machine configuration status on nodes.
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

| Variable                                | Default | Description                                                                  |
|-----------------------------------------|--|------------------------------------------------------------------------------|
| `post_rollback_checks`                  |  | Adds list of conditions to wait until the desired status is achieved.        |
| `post_rollback_expected_network_type`   |  | Check if CNI `OpenShiftSDN` was set after rollback.                          |
| `post_rollback_network_provider_config` |  | Checks if custom network configuration for `ovnKubernetesConfig` is deleted. |
| `post_rollback_namespace`               |  | Checks if namespace `openshift-ovn-kubernetes` is deleted after rollback.    |

> Override variables in a host-vars/group-vars file or with `-e`.

---

## Dependencies

* No external roles.

---

## Example playbook

```yaml
---
- name: Post Rollback
  hosts: localhost
  gather_facts: false
  roles:
    - role: network.offline_migration_sdn_to_ovnk.post_rollback
      vars:
        post_rollback_checks:
          - "oc wait co --all --for='condition=Available=True' --timeout=60s"
          - "oc wait co --all --for='condition=Progressing=False' --timeout=60s"
          - "oc wait co --all --for='condition=Degraded=False' --timeout=60s"
          - "oc wait mcp --all --for='condition=UPDATED=True' --timeout=60s"
          - "oc wait mcp --all --for='condition=UPDATING=False' --timeout=60s"
          - "oc wait mcp --all --for='condition=DEGRADED=False' --timeout=60s"
        post_rollback_network_provider_config: ovnKubernetesConfig
        post_rollback_namespace: openshift-ovn-kubernetes
        post_rollback_expected_network_type: OpenShiftSDN
        post_rollback_verify_machine_config_timeout: 300
        post_rollback_clean_migration_timeout: 120
```

## License

Apache-2.0

## Authors

@miheer