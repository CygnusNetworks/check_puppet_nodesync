# check_puppet_nodesync

This Nagios/Icinga check provides a check for the node synchronization 
of Puppet Nodes querying directly the PuppetDB. It will report nodes, 
which have not reported back to the Puppetserver or nodes which have failed runs.

## Dependencies

The check uses Python3 and the following Python modules:

  * pypuppetdb - choose correct version for your PuppetDB version
  * nagiosplugin
  
## Installation

```
pip3 install nagiosplugin pypuppetdb
python3 setup.py install
```

Be sure to select the corret pypuppetdb version for your PuppetDB.

## Usage

The check usages a PuppetDB on localhost:8080 by default. You will get 
a help using:

```
check_puppet_nodesync -h
```

A successful run would show something like this:

```
PUPPETNODESYNC CRITICAL - Hosts: host1.something.com,host2.something.com failed | nodes_changed=58 nodes_failed=2 nodes_ignored=0 nodes_in_sync=221 nodes_no_sync=3 nodes_total=226 nodes_unchanged=164
```

## TODO

  * PuppetDB SSL Cert connections
  * Python 2.x support
  
  