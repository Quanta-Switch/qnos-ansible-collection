#!/usr/bin/python
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.
#
from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'network'}


DOCUMENTATION = """
---
module: qnos_system
version_added: "2.9"
author: "Peter Sprygada (@privateip)"
short_description: Manage the system attributes on Quanta Switch
description:
  - This module provides declarative management of node system attributes
    on Quanta Switch.  It provides an option to configure host system
    parameters or remove those parameters from the device active
    configuration.
notes:
  - Tested against QNOS Switch
options:
  hostname:
    description:
      - Configure the device hostname parameter. This option takes an ASCII string value.
    type: str
  domain_name:
    description:
      - Configure the IP domain name
        on the remote device to the provided value. Value
        should be in the dotted name form and will be
        appended to the C(hostname) to create a fully-qualified
        domain name.
    type: list
  domain_search:
    description:
      - Provides the list of domain suffixes to
        append to the hostname for the purpose of doing name resolution.
        This argument accepts a list of names and will be reconciled
        with the current active configuration on the running node.
    type: list
  lookup_enabled:
    description:
      - Administrative control
        for enabling or disabling DNS lookups.  When this argument is
        set to True, lookups are performed and when it is set to False,
        lookups are not performed.
    type: bool
  name_servers:
    description:
      - List of DNS name servers by IP address to use to perform name resolution
        lookups.  This argument accepts either a list of DNS servers See
        examples.
    type: list
  state:
    description:
      - State of the configuration
        values in the device's current active configuration.  When set
        to I(present), the values should be configured in the device active
        configuration and when set to I(absent) the values should not be
        in the device active configuration
    type: str
    default: present
    choices: ['present', 'absent']
"""

EXAMPLES = """
- name: configure hostname and domain name
  qnos_system:
    hostname: qnos01
    domain_name: test.example.com
    domain_search:
      - ansible.com
      - redhat.com

- name: remove configuration
  qnos_system:
    name_servers:
      - 192.0.2.1
      - 192.0.2.2
      - 192.0.2.3
    state: absent

- name: configure name servers
  qnos_system:
    name_servers:
      - 8.8.8.8
      - 8.8.4.4
"""

RETURN = """
commands:
  description: The list of configuration mode commands to send to the device
  returned: always
  type: list
  sample:
    - hostname qnos01
    - ip domain-name test.example.com
"""
import re

from ansible.module_utils.basic import AnsibleModule
try:
    from library.module_utils.network.qnos.qnos import get_config, load_config
except ImportError:
    from ansible.module_utils.network.qnos.qnos import get_config, load_config
from ansible.module_utils.network.common.utils import ComplexList


_CONFIGURED_VRFS = None


def has_vrf(module, vrf):
    global _CONFIGURED_VRFS
    if _CONFIGURED_VRFS is not None:
        return vrf in _CONFIGURED_VRFS
    config = get_config(module)
    _CONFIGURED_VRFS = re.findall(r'vrf definition (\S+)', config)
    return vrf in _CONFIGURED_VRFS


def requires_vrf(module, vrf):
    if not has_vrf(module, vrf):
        module.fail_json(msg='vrf %s is not configured' % vrf)


def diff_list(want, have):
    adds = [w for w in want if w not in have]
    removes = [h for h in have if h not in want]
    return (adds, removes)


def map_obj_to_commands(want, have, module):
    commands = list()
    state = module.params['state']

    def needs_update(x):
        return want.get(x) is not None and (want.get(x) != have.get(x))

    if state == 'absent':
        if have['hostname'] != 'Switch':
            commands.append('no hostname')

        if have['lookup_enabled'] is False:
            commands.append('ip domain-lookup')

        vrfs = set()
        for item in have['domain_name']:
            if item['vrf'] and item['vrf'] not in vrfs:
                vrfs.add(item['vrf'])
                commands.append('no ip domain-name vrf %s' % item['vrf'])
            elif None not in vrfs:
                vrfs.add(None)
                commands.append('no ip domain-name')

        vrfs = set()
        for item in have['domain_search']:
            if item['vrf'] and item['vrf'] not in vrfs:
                vrfs.add(item['vrf'])
                commands.append('no ip domain-list vrf %s' % item['vrf'])
            elif None not in vrfs:
                vrfs.add(None)
                commands.append('no ip domain-list')

        vrfs = set()
        for item in have['name_servers']:
            if item['vrf'] and item['vrf'] not in vrfs:
                vrfs.add(item['vrf'])
                commands.append('no ip name-server vrf %s' % item['vrf'])
            elif None not in vrfs:
                vrfs.add(None)
                commands.append('no ip name-server')

    elif state == 'present':
        if needs_update('hostname'):
            commands.append('hostname %s' % want['hostname'])

        if needs_update('lookup_enabled'):
            cmd = 'ip domain-lookup'
            if want['lookup_enabled'] is False:
                cmd = 'no %s' % cmd
            commands.append(cmd)

        if want['domain_name']:
            adds, removes = diff_list(want['domain_name'], have['domain_name'])
            for item in removes:
                if item['vrf']:
                    commands.append('no ip domain-name vrf %s %s' % (item['vrf'], item['name']))
                else:
                    commands.append('no ip domain-name %s' % item['name'])
            for item in adds:
                if item['vrf']:
                    requires_vrf(module, item['vrf'])
                    commands.append('ip domain-name vrf %s %s' % (item['vrf'], item['name']))
                else:
                    commands.append('ip domain-name %s' % item['name'])

        if want['domain_search']:
            adds, removes = diff_list(want['domain_search'], have['domain_search'])
            for item in removes:
                if item['vrf']:
                    commands.append('no ip domain-list vrf %s %s' % (item['vrf'], item['name']))
                else:
                    commands.append('no ip domain-list %s' % item['name'])
            for item in adds:
                if item['vrf']:
                    requires_vrf(module, item['vrf'])
                    commands.append('ip domain-list vrf %s %s' % (item['vrf'], item['name']))
                else:
                    commands.append('ip domain-list %s' % item['name'])

        if want['name_servers']:
            adds, removes = diff_list(want['name_servers'], have['name_servers'])
            for item in removes:
                if item['vrf']:
                    commands.append('no ip name-server vrf %s %s' % (item['vrf'], item['server']))
                else:
                    commands.append('no ip name-server %s' % item['server'])
            for item in adds:
                if item['vrf']:
                    requires_vrf(module, item['vrf'])
                    commands.append('ip name-server vrf %s %s' % (item['vrf'], item['server']))
                else:
                    commands.append('ip name-server %s' % item['server'])

    return commands


def parse_hostname(config):
    match = re.search(r'^hostname \s?"(.+)"', config, re.M)
    # match = re.search(r'^hostname (\S+)', config, re.M)
    if match is not None:
        return match.group(1)
    else:
        return None


def parse_domain_name(config):
    match = re.findall(r'^ip domain-name (?:vrf (\S+) )*"(.+)"', config, re.M)
    matches = list()
    for vrf, name in match:
        if not vrf:
            vrf = None
        matches.append({'name': name, 'vrf': vrf})
    return matches


def parse_domain_search(config):
    match = re.findall(r'^ip domain-list (?:vrf (\S+) )*"(.+)"', config, re.M)
    matches = list()
    for vrf, name in match:
        if not vrf:
            vrf = None
        matches.append({'name': name, 'vrf': vrf})
    return matches


def parse_name_servers(config):
    match = re.findall(r'^ip name-server (?:vrf (\S+) )*(.*)', config, re.M)
    matches = list()
    for vrf, servers in match:
        if not vrf:
            vrf = None
        for server in servers.split():
            matches.append({'server': server, 'vrf': vrf})
    return matches


def map_config_to_obj(module):
    config = get_config(module)
    return {
        'hostname': parse_hostname(config),
        'domain_name': parse_domain_name(config),
        'domain_search': parse_domain_search(config),
        'lookup_enabled': 'no ip domain-lookup' not in config,
        'name_servers': parse_name_servers(config)
    }


def map_params_to_obj(module):
    obj = {
        'hostname': module.params['hostname'],
        'lookup_enabled': module.params['lookup_enabled'],
    }

    domain_name = ComplexList(dict(
        name=dict(key=True),
        vrf=dict()
    ), module)

    domain_search = ComplexList(dict(
        name=dict(key=True),
        vrf=dict()
    ), module)

    name_servers = ComplexList(dict(
        server=dict(key=True),
        vrf=dict()
    ), module)

    for arg, cast in [('domain_name', domain_name),
                      ('domain_search', domain_search),
                      ('name_servers', name_servers)]:

        if module.params[arg]:
            obj[arg] = cast(module.params[arg])
        else:
            obj[arg] = None

    return obj


def main():
    """ Main entry point for Ansible module execution
    """
    argument_spec = dict(
        hostname=dict(),

        domain_name=dict(type='list'),
        domain_search=dict(type='list'),
        name_servers=dict(type='list'),

        lookup_enabled=dict(type='bool'),

        state=dict(choices=['present', 'absent'], default='present')
    )

    module = AnsibleModule(argument_spec=argument_spec,
                           supports_check_mode=True)

    result = {'changed': False}

    warnings = list()
    result['warnings'] = warnings

    want = map_params_to_obj(module)
    have = map_config_to_obj(module)

    commands = map_obj_to_commands(want, have, module)
    result['commands'] = commands

    if commands:
        if not module.check_mode:
            load_config(module, commands)
        result['changed'] = True

    module.exit_json(**result)


if __name__ == "__main__":
    main()
