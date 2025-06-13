.. _network.offline_migration_sdn_to_ovnk.check_nodes_ready_module:


*******************************************************
network.offline_migration_sdn_to_ovnk.check_nodes_ready
*******************************************************

**Check if all cluster nodes are in Ready state.**


Version added: 1.0.0

.. contents::
   :local:
   :depth: 1


Synopsis
--------
- Check if all cluster nodes are in Ready state.




Parameters
----------

.. raw:: html

    <table  border=0 cellpadding=0 class="documentation-table">
        <tr>
            <th colspan="1">Parameter</th>
            <th>Choices/<font color="blue">Defaults</font></th>
            <th width="100%">Comments</th>
        </tr>
            <tr>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>timeout</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">integer</span>
                    </div>
                </td>
                <td>
                        <b>Default:</b><br/><div style="color: blue">120</div>
                </td>
                <td>
                        <div>Timeout in seconds.</div>
                </td>
            </tr>
    </table>
    <br/>




Examples
--------

.. code-block:: yaml

    - name: Check if all cluster nodes are in Ready state
      network.offline_migration_sdn_to_ovnk.check_nodes_ready:
      register: node_status

    - name: Notify user about NotReady nodes
      ansible.builtin.debug:
        msg: >
          The following nodes are not in the Ready state:  {{ node_status.not_ready_nodes | map(attribute='name') | join(', ') }}.
          Please investigate machine config daemon pod logs.

      when: node_status.not_ready_nodes | length > 0



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
