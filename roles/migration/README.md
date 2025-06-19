# `migration` role

Part of the **network.offline_migration_sdn_to_ovnk** collection.

`network.offline_migration_sdn_to_ovnk` drives an **OpenShiftSDN → OVNKubernetes** network migration
(or the reverse rollback) on an OpenShift 4.x cluster.  
It automates the operator flag flips, cluster-operator health checks and
post-migration verification so that the change can be executed in a
controlled, reboot-based maintenance window without external connectivity.

Typical responsibilities include:
- Check all cluster operators are normal and mcp's are not in updating or degraded state.
- Check for conflicting CIDR ranges.
- Check if the cluster is configured with NetworkPolicy isolation mode.
- Patch Network.operator.openshift.io and wait for migration field to clear
- Check if NNCP CRD exists. If yes then check if nncp is on primary interface.
  If yes then delete the primary interface_name.
- If OCP version is >= 4.12, then check if disable auto migration is set, 
  if yes then don't perform auto migration of egress_ip, egress_firewall, multicast.
- Applies custom network settings like `mtu, geneve_port, ipv4_subnet` if provided.
- Wait until MCO starts applying new machine config to nodes.
- Wait for MCO to finish its work.
- Verify machine configuration status on nodes.
- Trigger OVN-Kubernetes deployment.
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

| Variable                            | Default           | Purpose                                                                                                                     |
|-------------------------------------|-------------------|-----------------------------------------------------------------------------------------------------------------------------|
| `migration_disable_auto_migration`  | `false`           | If `true`, for OCP >= 4.12 auto-migration of egress_ip, egress_firewall, multicast will happen.                             |
| `migration_mtu`                     | `1400`            | Desired cluster-wide MTU after the move.                                                                                    |
| `migration_geneve_port`             | `6081`            | Port used by OVN-Geneve tunnelling.                                                                                         |
| `migration_ipv4_subnet`             | `"100.64.0.0/16"` | Pod network block created if none exists.                                                                                   |
| `migration_egress_ip`               | `false`           | Enable OVN egress-IP feature right after the migration.                                                                     |
| `migration_egress_firewall`         | `false`           | Enable OVN egress-firewall feature.                                                                                         |
| `migration_multicast`               | `false`           | Enable multicast feature (OVN only).                                                                                        |
 | `migration_interface_name`          |                   | Primary interface name for the role to check if nncp was installed on it. If yes then it is deleted before migration to OVN |
 | `migration_network_type`            | | Set to OVNKubernetes i.e the desired CNI plugin to migrate                                                                  | 
| `migration_conflicting_cidr_ranges` || Provides `CIDR range` which is not allowed to migrate to CNI `OVNKubernetes`                                                |                                                           
| `migration_configure_network_type`  || Sets configuration field `ovnKubernetes` to add custom network configuration for OVNKubernetes.                             | 
| `migration_checks`                   || Adds list of conditions to wait until the desired status is achieved.                                                       |
> **Tip** – put customised values in a host-vars or extra-vars file and pass
> it with `-e @my_vars.yml`.

---

## Dependencies

* No external Ansible roles.

---

## Example playbook

```yaml
---
- name: Migrate from OpenShift SDN to OVN-Kubernetes
  hosts: localhost
  gather_facts: false
  roles:
    - role: network.offline_migration_sdn_to_ovnk.migration
      vars:
        migration_clean_migration_timeout: 120
        migration_change_migration_timeout: 120
        migration_network_type: OVNKubernetes
        migration_mcp_completion_timeout: 18000 # Timeout in seconds
        migration_ovn_co_timeout: 120 # Timeout in seconds
        migration_ovn_multus_timeout: 300 # Timeout in seconds for waiting for Multus pods
        migration_verify_machine_config_timeout: 300
        migration_conflicting_cidr_ranges:
          - "100.64.0.0/16"
          - "169.254.169.0/29"
          - "100.88.0.0/16"
          - "fd98::/64"
          - "fd69::/125"
          - "fd97::/64"
        migration_checks:
          - "oc wait co --all --for='condition=Available=True' --timeout=60s"
          - "oc wait co --all --for='condition=Progressing=False' --timeout=60s"
          - "oc wait co --all --for='condition=Degraded=False' --timeout=60s"
          - "oc wait mcp --all --for='condition=UPDATING=False' --timeout=60s"
          - "oc wait mcp --all --for='condition=DEGRADED=False' --timeout=60s"
        migration_disable_auto_migration: false # true enables disable_automatic_migration.
        # You will need to set migration_egress_ip, migration_egress_firewall and migration_multicast as follows:
        # migration_egress_ip: false
        # migration_egress_firewall: false
        # migration_multicast: false
        migration_configure_network_type: ovnKubernetes
        # migration_mtu: 1400
        # migration_geneve_port: 6081
        # migration_ipv4_subnet: "100.64.0.0/16"
        # Primary interface to check if nncp is installed on it.
        # migration_interface_name: eth0
```

## License

Apache-2.0

## Authors

Miheer Salunke @miheer