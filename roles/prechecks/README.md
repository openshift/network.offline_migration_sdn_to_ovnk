# `prechecks` role

Part of the **network.offline_migration_sdn_to_ovnk** collection.

Runs a **comprehensive readiness assessment** _before_ starting the
OpenShiftSDN → OVNKubernetes offline migration (or any rollback rehearsal).  
It surfaces blocking issues early so the actual cut-over window remains short
and predictable.

## What it does

- Check if oc client is installed and binary exists.
- Check if KUBECONFIG is set and file exists.
- Check if the current user is 'system:admin' or a user with cluster admin rights using custom module.

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

_No external roles are required._

---

## Example playbook

```yaml
---
- name: Prechecks
  hosts: localhost
  gather_facts: false
  roles:
    - role: network.offline_migration_sdn_to_ovnk.prechecks
```

## License

Apache-2.0

## Authors

@miheer