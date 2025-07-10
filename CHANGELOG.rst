=======================================================
Network.Offline\_Migration\_Sdn\_To\_Ovnk Release Notes
=======================================================

.. contents:: Topics

v1.0.3
======

Release Summary
---------------

Patch release focusing on adding important features during migration and fixing reboot speed.

Major Changes
-------------

- Feature to specify `routingViaHost` and `ipForwarding` in the gatewayConfig object during migration.
- Feature to specify a different cluster network IP address block.
- Reboot masters only in serial fashion and other nodes not having role master in parallel fashion.

Minor Changes
-------------

- Update the README file of the role reboot.
- Update the README file with the new features.

v1.0.2
======

Release Summary
---------------

Patch release focusing on suggestions as per ansible partners.

Bugfixes
--------

- Adds CHANGE log files for releasing v1.0.2
- Adds min required version od ansible to 2.18
- Fix README as per per ansible statndards
- Ignore files and folders not needed during build
- Use Python version min 3.12

v1.0.1
======

Release Summary
---------------

Patch release 1.0.1 focusing adding CI tests for performing galaxy import and adds missing documentation for roles.

Minor Changes
-------------

- Add `make import` target to Makefile.

Bugfixes
--------

- Fixes roles docxumentation.

v1.0.0
======

New Modules
-----------

- network.offline_migration_sdn_to_ovnk.change_network_type - Change the default network type (SDN ↔ OVN).
- network.offline_migration_sdn_to_ovnk.check_cidr_ranges - Checks for conflicting range with the provided list of range.
- network.offline_migration_sdn_to_ovnk.check_kubeconfig - Checks existence of KUBECONFIG file.
- network.offline_migration_sdn_to_ovnk.check_network_migration - Check if migration of cni was set to desired one i.e OpenShiftSDN or OVNKubernetes.
- network.offline_migration_sdn_to_ovnk.check_network_policy_mode - Checks if NetworkPolicy isolation mode has been set.
- network.offline_migration_sdn_to_ovnk.check_network_provider - Check if the CNI network provider is expected one.
- network.offline_migration_sdn_to_ovnk.check_nodes_ready - Check if all cluster nodes are in Ready state.
- network.offline_migration_sdn_to_ovnk.check_oc_client - Change the default network type (SDN ↔ OVN).
- network.offline_migration_sdn_to_ovnk.check_whoami - Checks if the user can perform all actions (indicating cluster-admin rights).
- network.offline_migration_sdn_to_ovnk.clean_migration_field - Patch Network.operator.openshift.io and wait for migration field to clear.
- network.offline_migration_sdn_to_ovnk.configure_network_settings - Configure network settings for migration or rollback.
- network.offline_migration_sdn_to_ovnk.delete_primary_nncp - If nncp is configured on primary interface then deletes it.
- network.offline_migration_sdn_to_ovnk.disable_automatic_migration - Disables auto migration of egress_ip, egress_firewall and multicast.
- network.offline_migration_sdn_to_ovnk.get_ocp_version - Fetches the OpenShift version.
- network.offline_migration_sdn_to_ovnk.manage_network_config - This module clears ups the old network config and the namespace for the old CNI.
- network.offline_migration_sdn_to_ovnk.patch_mcp_paused - Patch the machine config pool to pause or unpause.
- network.offline_migration_sdn_to_ovnk.reboot_nodes - Reboot Nodes.
- network.offline_migration_sdn_to_ovnk.resume_mcp - Unpauses the mcp after reboot.
- network.offline_migration_sdn_to_ovnk.trigger_network_type - Patches the networkType in the Network.config.openshift.io.
- network.offline_migration_sdn_to_ovnk.verify_cluster_operators_health - Verify if all cluster operators are healthy.
- network.offline_migration_sdn_to_ovnk.verify_machine_config - Verifies the machine configuration status after we trigger mco update using module change_network_type.
- network.offline_migration_sdn_to_ovnk.wait_for_mco - Checks if mcp's have started UPDATING.
- network.offline_migration_sdn_to_ovnk.wait_for_mco_completion - Wait for MCO to finish its work after change_network_type triggers mco update.
- network.offline_migration_sdn_to_ovnk.wait_for_network_co - Wait until the Network Cluster Operator is in PROGRESSING=True state.
- network.offline_migration_sdn_to_ovnk.wait_multus_restart - Checks if the multus pods are restarted successfully.
