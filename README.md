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
The `qnos` `cliconf` plugin provides the capabilities to use Ansible vendor agnostic modules (`cli_command` and `cli_config`) to automate against QUANTA Switches. Please refer to [Advanced Topics with Ansible for Network Automation](https://docs.ansible.com/ansible/latest/network/user_guide/index.html) for more detailed information.

Remember set `ansible_network_os` and `ansible_connection` correctly, i.e.:

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

### publish version
```
0.0.1   First publish
0.0.2   1. Remove "library" file
        2. Correct README.md contents.
        3. Correct cliconf/qnos.py path to "plugins.module_utils.network.qnos.qnos import QnosNetworkConfig"
``` 
