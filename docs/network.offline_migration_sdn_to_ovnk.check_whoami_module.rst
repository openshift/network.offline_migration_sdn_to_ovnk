.. _network.offline_migration_sdn_to_ovnk.check_whoami_module:


**************************************************
network.offline_migration_sdn_to_ovnk.check_whoami
**************************************************

**Checks if the user can perform all actions (indicating cluster-admin rights).**


Version added: 1.0.0

.. contents::
   :local:
   :depth: 1


Synopsis
--------
- Checks if the user can perform all actions (indicating cluster-admin rights).







Examples
--------

.. code-block:: yaml

    - name: Check if the current user is 'system:admin' or a user with cluster admin rights using custom module
      network.offline_migration_sdn_to_ovnk.check_whoami:
      register: oc_whoami_result

    - name: Show result of oc whoami check
      ansible.builtin.debug:
        msg: "The output of `oc whoami`: {{ oc_whoami_result.message }}"
      when: not oc_whoami_result.failed

    - name: Fail if `oc whoami` is not 'system:admin' or does not have cluster admin rights.
      ansible.builtin.fail:
        msg: "{{ oc_whoami_result.msg }}"
      when: oc_whoami_result.failed



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
