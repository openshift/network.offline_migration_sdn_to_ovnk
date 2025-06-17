# `reboot_nodes` role

Part of the **network.offline_migration_sdn_to_ovnk** collection.

Safely **reboots OpenShift cluster nodes** in a controlled,
batches-or-serial fashion, honouring *MachineConfigPool* topology and
ensuring that workloads stay available during the migration or rollback
process.

**Why this role exists**

* The **offline SDN → OVN-K** migration requires one (or more) full
  reboots for each node so the new MachineConfig takes effect.

This role encapsulates that logic with sensible defaults and tunable
variables.

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

| Variable | Default | Description |
|----------|---------|-------------|

---

## Dependencies

* No external roles.

---

## Example playbook

_Reboot all master nodes, followed by worker nodes, using the machine-config-daemon:_

```yaml
---
- name: Reboot master nodes
  network.offline_migration_sdn_to_ovnk.reboot_nodes:
    role: "master"
    namespace: "openshift-machine-config-operator"
    daemonset_label: "machine-config-daemon"
    delay: 1
    retries: 5
    retry_delay: 3
    timeout: 1800

- name: Reboot worker nodes
  network.offline_migration_sdn_to_ovnk.reboot_nodes:
    role: "worker"
    namespace: "openshift-machine-config-operator"
    daemonset_label: "machine-config-daemon"
    delay: 1
    retries: 5
    retry_delay: 3
    timeout: 1800
```

## License

Apache-2.0

## Authors

Miheer Salunke @miheer
