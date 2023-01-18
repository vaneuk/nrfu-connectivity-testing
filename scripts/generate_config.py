"""
Generates config templates based on ansible inventory group name
"""

import sys
import argparse
import pathlib

import yaml
from jinja2 import Environment, FileSystemLoader


def generate_config(config: dict, template_name: str, setup_name: str) -> None:
    template = env.get_template(f'{template_name}.j2')
    for host in config['hosts']:
        if 'data_ip' in config['hosts'][host]:
            host_ip = config['hosts'][host]['data_ip']
        else:
            host_ip = config['hosts'][host]['ansible_host']
        output = template.render(peers=config['hosts'][host]['peers'], host=host, host_ip=host_ip)
        with open(f'../config/{setup_name}/{host}_{template_name}.sh', 'w') as f:
            f.write(output)


def get_ip(config, dst):
    for host in config['hosts']:
        if host == dst:
            if 'data_ip' in config['hosts'][host]:
                return config['hosts'][host]['data_ip']
            return config['hosts'][host]['ansible_host']


def add_peers_variable(config: dict) -> None:
    for host in config['hosts']:
        config['hosts'][host]['dst_ip'] = list()
        config['hosts'][host]['peers'] = list()
        for d in config['hosts'][host]['dst']:
            config['hosts'][host]['dst_ip'].append(get_ip(config, d))
        for peer in zip(config['hosts'][host]['dst'], config['hosts'][host]['dst_ip']):
            config['hosts'][host]['peers'].append(peer)


def load_config(setup_name):
    inventory_dir = pathlib.Path('../inventory')
    inventory_files = [path for path in inventory_dir.iterdir() if path.is_file() and (path.suffix == '.yaml' or path.suffix == '.yml')]
    for inventory_file in inventory_files:
        with open(inventory_file, 'r') as f:
            config = yaml.safe_load(f)
            if setup_name in config:
                print(f'Setup {setup_name} found in file {inventory_file}')
                return config[setup_name]
    print(f'Setup {setup_name} not found!')
    sys.exit(1)


def main(setup_name):
    config = load_config(setup_name)
    add_peers_variable(config)
    pathlib.Path(f'../config/{setup_name}').mkdir(exist_ok=True)
    generate_config(config, 'iptables', setup_name)
    generate_config(config, 'syslog', setup_name)
    generate_config(config, 'tcp', setup_name)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("setup_name", help="name of ansible inventory group to run tests on")
    args = parser.parse_args()

    file_loader = FileSystemLoader('../config_templates')
    env = Environment(loader=file_loader)
    main(args.setup_name)
