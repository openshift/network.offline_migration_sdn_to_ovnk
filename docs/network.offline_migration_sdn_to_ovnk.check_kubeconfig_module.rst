.. _network.offline_migration_sdn_to_ovnk.check_kubeconfig_module:


******************************************************
network.offline_migration_sdn_to_ovnk.check_kubeconfig
******************************************************

**Checks existence of KUBECONFIG file.**


Version added: 1.0.0

.. contents::
   :local:
   :depth: 1


Synopsis
--------
- Checks existence of KUBECONFIG file.







Examples
--------

.. code-block:: yaml

    - name: Check if KUBECONFIG is set and file exists
      network.offline_migration_sdn_to_ovnk.check_kubeconfig:
      register: kubeconfig_result



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
