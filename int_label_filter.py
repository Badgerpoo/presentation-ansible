#!/usr/bin/env python
#
# Interface labelling using CDP neighbour details
#

import sys,os,re

'''
cdp_neighbors = {
  "response": [
    {
      "destination_host": "ccr1.domain",
      "local_port": "GigabitEthernet1/0/49",
      "management_ip": "137.222.12.250",
      "platform": "cisco WS-C4506-E",
      "remote_port": "GigabitEthernet3/5",
      "software_version": "Cisco IOS Software, Catalyst 4500 L3 Switch  Software (cat4500e-UNIVERSALK9-M), Version 15.2(2)E1, RELEASE SOFTWARE (fc3)"
    },
    {
      "destination_host": "ccs53.domain",
      "local_port": "GigabitEthernet1/0/16",
      "management_ip": "172.17.51.57",
      "platform": "cisco WS-C2960X-48LPS-L",
      "remote_port": "GigabitEthernet1/0/48",
      "software_version": "Cisco IOS Software, C2960X Software (C2960X-UNIVERSALK9-M), Version 15.2(2)E3, RELEASE SOFTWARE (fc3)"
    }
  ],
}

int_descriptions = {
  "response": [
    {
      "duplex": "auto",
      "name": "SDN",
      "port": "Gi1/0/1",
      "speed": "auto",
      "status": "notconnect",
      "type": "10/100/1000BaseTX",
      "vlan": "12"
    },
    {
      "duplex": "a-full",
      "name": "ccs53-Gi1/0/48",
      "port": "Gi1/0/16",
      "speed": "a-1000",
      "status": "connected",
      "type": "10/100/1000BaseTX",
      "vlan": "trunk"
    },
    {
      "duplex": "a-full",
      "name": "ccr1-Gi3/4 (M0n)",
      "port": "Gi1/0/49",
      "speed": "a-1000",
      "status": "connected",
      "type": "10/100/1000BaseTX SFP",
      "vlan": "trunk"
    },
  ]
}
'''

int_names = {
  'cisco_ios': {
    'Fa': 'FastEthernet',
    'Gi': 'GigabitEthernet',
    'Te': 'TenGigabitEthernet',
    'Po': 'Port-channel',
  }
}

class FilterModule(object):
  def filters(self):
    return {
      'int_label': int_label
    }

def int_label(cdp_neighbors,int_descriptions):
  '''
  Take in facts and generate suitable interface labels
  '''

  '''
  1. Generate required labels
  '''

  new_int_description = {}
  for item in cdp_neighbors['response']:

    # Convert long int name to short version
    split_int = re.split('(\d+.*)', item['remote_port'])
    # short_int_name = int_names['cisco_ios'][split_int[0]] + split_int[1]
    short_int_name = split_int[0][:2] + split_int[1]

    # Strip FQDN off the remote host
    split_host = re.split('\.', item['destination_host'])

    # Required interface description:
    new_int_description[item['local_port']] = (split_host[0] + '-' + short_int_name)
    '''
    new_int_description looks like this:
    {
      'GigabitEthernet1/0/16': 'ccs53-Gi1/0/48',
      'GigabitEthernet1/0/49': 'ccr1-Gi3/5'
    }
    '''

  '''
  2. Check existing labels
  '''

  old_int_description = {}
  for item in int_descriptions['response']:
    # Convert short form int to long
    split_int = re.split('(\d+.*)', item['port'])
    long_int_name = int_names['cisco_ios'][split_int[0]] + split_int[1]

    old_int_description[long_int_name] = item['name']
    '''
    old_int_description looks like this:
    {
      'GigabitEthernet1/0/1': 'SDN',
      'GigabitEthernet1/0/49': 'ccr1-Gi3/5',
      'GigabitEthernet1/0/16': 'ccs53-Gi1/0/48'
    }
    '''

  return_descs = {}

  '''
  3. Check new generated labels against existing ones, then return a dictionary
     of the differences
  '''
  for interface in new_int_description:
    # Preserve any comment in parenthesis
    interface_description, delimiter, comment = old_int_description[interface].partition(" ")
    if re.search('\(.*\)', comment):
      # Standardise the various MONs
      if re.search('\(m(o|0)n\)', comment, re.I):
        comment = '(MON)'
      new_int_description[interface] += delimiter + comment
    # Add MON to any link connecting to core routers
    elif re.search('^br[1234]-\S+$', new_int_description[interface]):
      new_int_description[interface] += ' (MON)'

    # Build dict of interfaces to correct
    if new_int_description[interface] != old_int_description[interface]:
      return_descs[interface] = new_int_description[interface]
      '''
      return_descs looks like this:
      {
        'GigabitEthernet1/0/49': 'ccr1-Gi3/5'
      }
      '''

  return return_descs

'''
if __name__ == '__main__':
  print(int_label(cdp_neighbors,int_descriptions))
'''