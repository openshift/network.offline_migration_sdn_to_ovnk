.. _network.offline_migration_sdn_to_ovnk.check_oc_client_module:


*****************************************************
network.offline_migration_sdn_to_ovnk.check_oc_client
*****************************************************

**Change the default network type (SDN ↔ OVN).**


Version added: 1.0.0

.. contents::
   :local:
   :depth: 1


Synopsis
--------
- Switches the cluster DefaultNetwork between ``OpenShiftSDN`` and ``OVNKubernetes`` by patching the Network.operator CR.







Examples
--------

.. code-block:: yaml

    - name: Check if oc client is installed and binary exists
      network.offline_migration_sdn_to_ovnk.check_oc_client:
      register: oc_check_result

    - name: Display oc client version
      ansible.builtin.debug:
        msg: "OpenShift client version: {{ oc_check_result.version }}"
      when: oc_check_result.version is defined

    - name: Fail if oc binary or client is not installed or functional
      ansible.builtin.fail:
        msg: "{{ oc_check_result.msg }}"
      when: not oc_check_result.version



Return Values
-------------
Common return values are documented `here <https://docs.ansible.com/ansible/latest/reference_appendices/common_return_values.html#common-return-values>`_, the following are the fields unique to this module:

.. raw:: html

    <table border=0 cellpadding=0 class="documentation-table">
        <tr>
            <th colspan="1">Key</th>
            <th>Returned</th>
            <th width="100%">Description</th>
        </tr>
            <tr>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="return-"></div>
                    <b>changed</b>
                    <a class="ansibleOptionLink" href="#return-" title="Permalink to this return value"></a>
                    <div style="font-size: small">
                      <span style="color: purple">boolean</span>
                    </div>
                </td>
                <td>always</td>
                <td>
                            <div>Whether the CR was modified.</div>
                    <br/>
                </td>
            </tr>
    </table>
    <br/><br/>


Status
------


Authors
~~~~~~~

- Miheer Salunke (@miheer)
