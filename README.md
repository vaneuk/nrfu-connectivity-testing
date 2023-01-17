# nrfu-connectivity-testing
Ansible playbooks to run traffic flows between VMs and measure traffic dusruption duration when performing failover/HA testing during Network Ready For Use (NRFU) tests. 

sendip package is used to send TCP SYN packets with src port sequentially changing from 5000 to 5100, so traffic flows should be hashed to all available ECMP paths. Traffic flows are not bidirectional, so this playbooks can not be used to test traffic symmetry (for example in case there is ECMP through multiple Firewalls).

Packet arrival is registered using iptables.

## Installation
This playbook has been tested with python 3.9 and packages described in requirements.txt.
```
python3.9 -m venv venv                                                                   
source venv/bin/activate
python -m pip install -r requirements.txt
```

## Usage
Prerequisites:
- Configure ansible inventory, refer to the example in [example inventory](inventory/example_inventory.yaml).
- Configure username and sudo password in ansible group vars. Sudo password is used only once to enable passwordless sudo ("%sudo ALL=(ALL) NOPASSWD: ALL" will be added to /etc/sudoers). Refer to the example in [example group_vars file](inventory/example_inventory.yaml).


Generate configs for the setup:
```
cd scripts
python generate_config.py example_setup
```
Command line argument "example_setup" is the name of ansible inventory group to run tests on.

Perform initial VM config:
```
cd playbooks
ansible-playbook init.yml --extra-vars "setup_name=example_setup"
```

Run test:
```
cd playbooks
ansible-playbook run_test.yml --extra-vars "setup_name=example_setup duration=10"
```
"duration" is test duration in seconds

## Example
### Topology
Traffic flows are configured in ansible inventory file. The following traffic flows are present in [example_inventory.yaml](inventory/example_inventory.yaml).
```
 ┌───────────────────────────────────────────────────────┐
 │                                                       │
 │     ┌────────────────────────────────────────┐        │
 │     │                                        │        │
 │     │    ┌────────┐        ┌────────┐        │        │
 │     │    │        │        │        │        │        │
┌▼─────▼────▼──┐  ┌──▼────────▼──┐  ┌──▼────────▼──┐  ┌──▼───────────┐
│ example-vm-1 │  │ example-vm-2 │  │ example-vm-3 │  │ example-vm-4 │
└──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘
```

### Output
This is an example test output:
- "lost" is packets lost (rx - tx)
- "loss_duration" is packet loss duration in seconds (lost/rate)
```
+------------------------------+--------+------+------+--------+-----------------+
| flow                         |   rate |   tx |   rx |   lost |   loss_duration |
+==============================+========+======+======+========+=================+
| example-vm-1 -> example-vm-2 |  290.9 | 2909 | 2909 |      0 |               0 |
+------------------------------+--------+------+------+--------+-----------------+
| example-vm-2 -> example-vm-1 |  315   | 3150 | 3150 |      0 |               0 |
+------------------------------+--------+------+------+--------+-----------------+
| example-vm-1 -> example-vm-3 |  292.1 | 2921 | 2921 |      0 |               0 |
+------------------------------+--------+------+------+--------+-----------------+
| example-vm-3 -> example-vm-1 |  308.1 | 3081 | 3081 |      0 |               0 |
+------------------------------+--------+------+------+--------+-----------------+
| example-vm-1 -> example-vm-4 |  290.4 | 2904 | 2904 |      0 |               0 |
+------------------------------+--------+------+------+--------+-----------------+
| example-vm-4 -> example-vm-1 |  233.6 | 2336 | 2336 |      0 |               0 |
+------------------------------+--------+------+------+--------+-----------------+
| example-vm-2 -> example-vm-3 |  313.5 | 3135 | 3135 |      0 |               0 |
+------------------------------+--------+------+------+--------+-----------------+
| example-vm-3 -> example-vm-2 |  309.6 | 3096 | 3096 |      0 |               0 |
+------------------------------+--------+------+------+--------+-----------------+
```
