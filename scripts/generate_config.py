"""
Generates config templates based on ansible inventory group name
"""

import sys
import argparse
import pathlib

import json
import yaml
from jinja2 import Environment, FileSystemLoader

IPERF_SERVER_START_PORT = 5200
IPERF_PORT_START = 5200
TEMPLATES = {
    'sendip': ['iptables', 'syslog', 'sendip'],
    'iperf': ['iperf_server', 'iperf_client']
}


def generate_config(config: dict, template_name: str, setup_name: str) -> None:
    template = env.get_template(f'{template_name}.j2')
    for host in config:
        output = template.render(peers=config[host]['peers'], host=host, host_ip=config[host]['ansible_host'])
        with open(f'../config/{setup_name}/{host}_{template_name}.sh', 'w') as f:
            f.write(output)


def add_peers_dest_ip(config: dict) -> None:
    for host in config:
        for peer in config[host]['peers']:
            if config[host]['peers'][peer] is None:
                config[host]['peers'][peer] = dict()
            # when NAT is used ip is already defnied in config
            if 'ip' not in config[host]['peers'][peer]:
                config[host]['peers'][peer]['ip'] = config[peer]['ansible_host']


def add_iperf_ports_variable(config: dict) -> None:
    # client ports
    port = IPERF_PORT_START
    for host in config:
        for peer in config[host]['peers']:
            if 'client_port' not in config[host]['peers'][peer]:
                config[host]['peers'][peer]['client_port'] = str(port)
                port += 1
    # server ports
    for host in config:
        for peer in config[host]['peers']:
            config[host]['peers'][peer]['server_port'] = config[peer]['peers'][host]['client_port']


    # for host in config:
    #     for peer in config[host]['peers']:
    #         config[host]['peers'][peer]['server_port'] = str(port)
    #         port += 1
    # # client ports
    # for host in config:
    #     for peer in config[host]['peers']:
    #         config[host]['peers'][peer]['client_port'] = config[peer]['peers'][host]['server_port']


def load_config(setup_name):
    inventory_dir = pathlib.Path('../inventory')
    inventory_files = [path for path in inventory_dir.iterdir() if path.is_file() and (path.suffix == '.yaml' or path.suffix == '.yml')]
    for inventory_file in inventory_files:
        with open(inventory_file, 'r') as f:
            config = yaml.safe_load(f)
            if setup_name in config:
                print(f'Setup {setup_name} found in file {inventory_file}')
                return config[setup_name]['hosts']
    print(f'Setup {setup_name} not found!')
    sys.exit(1)


def config_sanity_check(config):
    failed = False
    for host in config:
        for peer in config[host]['peers']:
            if host not in config[peer]['peers']:
                print(f'unidirectional flow! {host} -> {peer} is defined, but {peer} -> {host} is not defined')
                failed = True
    if failed:
        sys.exit(1)


def main(setup_name: str, mode: str):
    config = load_config(setup_name)
    config_sanity_check(config)
    add_peers_dest_ip(config)
    pathlib.Path(f'../config/{setup_name}').mkdir(exist_ok=True)
    if mode == "iperf":
        add_iperf_ports_variable(config)
        print(json.dumps(config, indent=4, sort_keys=True))

    for template in TEMPLATES[mode]:
        generate_config(config, template, setup_name)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("setup_name", help="name of ansible inventory group to run tests on")
    parser.add_argument("mode", help="iperf or sendip")
    args = parser.parse_args()

    file_loader = FileSystemLoader('../config_templates')
    env = Environment(loader=file_loader)
    main(args.setup_name, args.mode)
