import argparse

from tabulate import tabulate
from generate_config import load_config
import sys, traceback


def get_result(data: dict) -> str:
    header = data[0].keys()
    rows = [x.values() for x in data]
    r = tabulate(rows, header, tablefmt='grid')
    return r


def get_iptables_data(config: dict, dir_name: str, setup_name: str, protocol: str) -> None:
    iptables_data = {}
    for host in config:
        iptables_data[host] = dict()
        with open(f'../tests/{setup_name}/{dir_name}/{host}.log') as f:
            for line in f.readlines():
                if 'LOG' in line and protocol in line:
                    line_list = line.strip().split(' ')
                    pckts = int(line_list[0])
                    peer = line_list[-1][2:-5]
                    direction = line_list[-1][-4:-2]
                    if peer not in iptables_data[host]:
                        iptables_data[host][peer] = dict()
                    iptables_data[host][peer][direction] = pckts

    return iptables_data


def add_flow_record(summary_data: list, flow: str, flows: list, duration: int, tx: int, rx: int) -> None:
    if flow not in flows:
        rate = tx/duration
        lost = tx - rx
        try:
            loss_duration = round(lost / rate, 2)
        except ZeroDivisionError:
            print(f'ERROR. Zero counters for flow: {flow}, rate: {rate}, tx: {tx}, rx: {rx}, lost: {lost}')
            loss_duration = 'ERROR'
        summary_data.append({'flow': flow, 'rate': rate, 'tx': tx, 'rx': rx, 'lost': lost, 'loss_duration': loss_duration})
        flows.append(flow)


def main(setup_name, dir_name, duration, protocol):
    config = load_config(setup_name)

    iptables_data = get_iptables_data(config, dir_name, setup_name, protocol)
    summary_data = []
    flows = []
    for host in iptables_data:
        for peer in iptables_data[host]:
            try:
                flow = f'{host} -> {peer}'
                add_flow_record(summary_data, flow, flows, duration, iptables_data[host][peer]['tx'], iptables_data[peer][host]['rx'])
                # reverse flow
                flow = f'{peer} -> {host}'
                add_flow_record(summary_data, flow, flows, duration, iptables_data[peer][host]['tx'], iptables_data[host][peer]['rx'])
            except KeyError:
                print(f'Failed to find flow: host={host}, peer={peer}. Check that traffic flows defined in inventory are bidirectional.')
                s = ("Consider adding the following to the inventory file:\n"
                     f"    {peer}:\n"
                     "      dst:\n"
                     f"        - {host}\n\n"
                     "Then run generate_config.py, ansible-playbook init.yml and rer-run the test.")
                print(s)
                traceback.print_exc()
                sys.exit(1)
    result = get_result(summary_data)
    print(result)
    with open(f'../tests/{setup_name}/{dir_name}/summary.log', 'w') as f:
        f.write(result)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("setup_name")
    parser.add_argument("dir")
    parser.add_argument("duration")
    parser.add_argument("protocol")

    args = parser.parse_args()
    main(args.setup_name, args.dir, int(args.duration), args.protocol)
