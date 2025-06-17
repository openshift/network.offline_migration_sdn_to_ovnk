# `rollback` role

Part of the **network.offline_migration_sdn_to_ovnk** collection.

Rolls an OpenShift 4.x cluster **back from OVNKubernetes to OpenShiftSDN** in an **offline / maintenance-window** scenario.  
It is the inverse of the main *migration* workflow and must be executed if a cut-over fails or post-migration validation exposes critical regressions.

---

## What the role does

- Fail if OpenShift version is 4.17 (Rollback Not Supported).
- Pause updates for master MachineConfigPool.
- Pause updates for worker MachineConfigPool.
- Patch Network.operator.openshift.io and wait for migration field to clear.
- Change network type to trigger MCO update.
- Trigger OpenshiftSDN deployment
- If OCP version is >= 4.12, then check if disable auto migration is set, 
  if yes then don't perform auto migration of egress_ip, egress_firewall, multicast.
- Customize network settings for mtu and vxlanPort if parameters are provided.
- Wait until the Network Cluster Operator is in PROGRESSING=True state.
- Wait for Multus pods to restart.
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

| Variable                          | Default | Description                                                                                     |
|-----------------------------------|---------|-------------------------------------------------------------------------------------------------|
| `rollback_network_type`           |         | Set to OpenShiftSDN i.e the desired CNI plugin to rollback.                                     |
| `rollback_disable_auto_migration` | `false` | If `true`, for OCP >= 4.12 auto-migration of egress_ip, egress_firewall, multicast will happen. |
| `rollback_mtu`                    | `1400`            | Desired cluster-wide MTU after the move.                                                        |
| `rollback_vxlanPort`              |  | Sets custom vxlanPort.                                                                          |
| `rollback_egress_ip`              | `false`           | Enable OVN egress-IP feature right.                                                             |
| `rollback_egress_firewall`        | `false`           | Enable OVN egress-firewall feature.                                                             |
| `rollback_multicast`              | `false`           | Enable multicast feature.                                                                       |
 | `rollback_network_type`           | | Set to OpenShiftSDN i.e the desired CNI plugin to rollback.                                     | 
| `rollback_configure_network_type` || Sets configuration field `openshiftSDN` to add custom network configuration for OpenShiftSDN.   | 

> **Tip –** put non-default overrides in `group_vars/all.yml` or pass at runtime with `-e`.

---

## Dependencies

_The role has no external role dependencies._

---

## Example playbook

```yaml
---
- name: Rollback
  hosts: localhost
  gather_facts: false
  roles:
    - role: network.offline_migration_sdn_to_ovnk.rollback
      vars:
        rollback_clean_migration_timeout: 120
        rollback_change_migration_timeout: 120
        rollback_network_type: OpenShiftSDN
        rollback_sdn_co_timeout: 120 # Timeout in seconds
        rollback_sdn_multus_timeout: 300 # Timeout in seconds for waiting for Multus pods
        rollback_disable_auto_migration: false # true enables disable_automatic_migration.
        # You will need to set rollback_egress_ip, rollback_egress_firewall and rollback_multicast as follows:
        # rollback_egress_ip: false
        # rollback_egress_firewall: false
        # rollback_multicast: false
        rollback_configure_network_type: openshiftSDN
        # rollback_mtu: 1400
        # rollback_vxlanPort: 4790
```

## License

Apache-2.0

## Authors

@miheer