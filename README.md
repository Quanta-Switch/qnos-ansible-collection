##	The purpose of QNOS modules
Ansible is a popular tool to help you automate I.T. process e.g. provision IT resources, deploy application and network configurations.

## Install the collection
The collection_path is a path which you want to install the collection.
```
ansible-galaxy collection install quantasw.qnos -p "collection_path"
```
P.S. The install command automatically appends the path ansible_collections to the one specified with the -p option unless the parent directory is already in a folder called ansible_collections.

The detail install instruction can refer [Installing collections](https://docs.ansible.com/ansible/latest/user_guide/collections_using.html#collections)

## Setting PYTHONPATH
Set your PYTHONPATH contains this "collection_path".
```
export PYTHONPATH=~/ansible/lib:~/ansible/test:collection_path/ansible_collections/quantasw/qnos
```
## QNOS `network_cli` platform
Set `ansible_network_os` and `ansible_connection` correctly in inventory file, i.e.:

```yaml
ansible_network_os=qnos
ansible_connection=network_cli
```
## Setting ansible.cfg
Add `qnos` to the variable `network_group_modules`
```yaml
inventory      = your host list
stdout_callback = yaml
module_utils = collection_path/ansible_collections/quantasw/qnos/plugins/module_utils
action_plugins = collection_path/ansible_collections/quantasw/qnos/plugins/module_utils/action
terminal_plugins = collection_path/ansible_collections/quantasw/qnos/plugins/module_utils/terminal
cliconf_plugins = collection_path/ansible_collections/quantasw/qnos/plugins/module_utils/cliconf
network_group_modules = eos, nxos, ios, iosxr, junos, vyos, qnos
```

The following is an example task which uses `cli_command` module:
```yaml
---
- name: get output for single command
  cli_command:
    command: show version
  register: result
```

The following is an example task which uses `cli_config` module:
```yaml
---
- name: setup
  cli_config:
    config: |
      interface loopback 0
      no description
      shutdown
    diff_match: none
```

## Using QNOS modules
QNOS Ansible modules provide additional functionality to help managing/configuring QUANTA Switches.

The following is an example task which uses `qnos_system` module to add `ansible.com` and `redhat.com` to the `ip domain-list`. (must add collection namespace in each QNOS modules)
```yaml
---
- name: configure domain_search
  quantasw.qnos.qnos_system:
    domain_search:
      - ansible.com
      - redhat.com
  register: result
```
The following is an example task which uses `qnos_reboot` to reboot the switch. The `confirm` option set to true if you're sure you want to reboot.
The `save` option set to yes if you're sure to save the running-config to the startup-config at rebooting.
```yaml
---
- name: reboot the device
  qnos_reboot:
    confirm: yes
    save: no
```
### publish version
```
0.0.1   First publish
0.0.2   1. Remove "library" file
        2. Correct README.md contents.
        3. Correct cliconf/qnos.py path to "plugins.module_utils.network.qnos.qnos import QnosNetworkConfig"
``` 
