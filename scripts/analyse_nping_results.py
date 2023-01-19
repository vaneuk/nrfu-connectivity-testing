import argparse

from tabulate import tabulate
from generate_config import load_config
from typing import Dict
import sys, traceback


def get_result(data: dict) -> str:
    header = next(iter(data.values())).keys()  # get keys of first value of dict
    # header = data[0].keys()
    rows = [x.values() for x in data.values()]
    r = tabulate(rows, header, tablefmt='grid')
    return r


def flatten_detailed_records(flows_detail: dict):
    result = {}
    for flow, flow_detail in flows_detail.items():
        for port, port_detail in flow_detail.items():
            key = f'{flow} -> {port}'
            result[key] = port_detail
    return result


def get_iptables_data_with_flows(config: dict, dir_name: str, setup_name: str) -> Dict:
    iptables_data = {}
    for host in config['hosts']:
        entry = {}
        with open(f'../tests/{setup_name}/{dir_name}/{host}.log') as f:
            for line in f.readlines():
                if '/*' in line:
                    line_list = line.strip().split(' ')
                    pckts = int(line_list[0])
                    comment = line_list[-2].replace("[", "").replace("]", "")
                    peer, direction, port = comment.split("_")
                    if peer not in entry:
                        entry[peer] = {}
                    if port not in entry[peer]:
                        entry[peer][port] = {}
                    entry[peer][port][direction] = pckts
        iptables_data[host] = entry

    return iptables_data


def find_loss_duration(iptables_data: dict, host: str, peer: str, delay: float) -> (float, float):
    lost_packets_for_flows = []
    for port in iptables_data[host][peer]:
        lost_packets = iptables_data[host][peer][port]['tx'] - iptables_data[peer][host][port]['rx']
        lost_packets_for_flows.append(lost_packets)
    min_loss_duration = min(lost_packets_for_flows) * delay
    max_loss_duration = max(lost_packets_for_flows) * delay
    return min_loss_duration, max_loss_duration


def add_summary_flow_record(summary_flow_records, iptables_data, host, peer, delay):
    flow = f'{host} -> {peer}'
    if flow not in summary_flow_records:
        min_loss_duration, max_loss_duration = find_loss_duration(iptables_data, host, peer, delay)
        summary_flow_records[flow] = {
            'flow': flow,
            'min_loss_duration': min_loss_duration,
            'max_loss_duration': max_loss_duration
        }


def add_detailed_flow_record(detailed_flow_records, iptables_data, host, peer, delay):
    flow = f'{host} -> {peer}'
    if flow not in detailed_flow_records:
        detailed_flow_records[flow] = {}
        for port in iptables_data[host][peer]:
            lost_packets = iptables_data[host][peer][port]['tx'] - iptables_data[peer][host][port]['rx']
            loss_duration = lost_packets * delay
            detailed_flow_records[flow][port] = {
                'flow': flow,
                'port': port,
                'tx': iptables_data[host][peer][port]['tx'],
                'rx': iptables_data[peer][host][port]['rx'],
                'lost': lost_packets,
                'loss_duration': loss_duration,
            }


def main(setup_name, dir_name, delay):
    config = load_config(setup_name)
    # convert from ms to seconds
    delay = delay / 1000

    iptables_data = get_iptables_data_with_flows(config, dir_name, setup_name)
    summary_flow_records = {}
    detailed_flow_records = {}
    for host, host_data in iptables_data.items():
        for peer, peer_data in host_data.items():
            add_summary_flow_record(summary_flow_records, iptables_data, peer, host, delay)
            add_summary_flow_record(summary_flow_records, iptables_data, host, peer, delay)
            add_detailed_flow_record(detailed_flow_records, iptables_data, peer, host, delay)
            add_detailed_flow_record(detailed_flow_records, iptables_data, host, peer, delay)
    result = get_result(summary_flow_records)
    flattened_flows_detail = flatten_detailed_records(detailed_flow_records)
    detailed_result = get_result(flattened_flows_detail)

    with open(f'../tests/{setup_name}/{dir_name}/summary.log', 'w') as f:
        f.write(result)
    with open(f'../tests/{setup_name}/{dir_name}/details.log', 'w') as f:
        f.write(detailed_result)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("setup_name")
    parser.add_argument("dir")
    parser.add_argument("delay")

    args = parser.parse_args()
    main(args.setup_name, args.dir, int(args.delay))
