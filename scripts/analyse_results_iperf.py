
import json
import argparse
import sys
import traceback
from tabulate import tabulate
from generate_config import load_config


class Flow():
    def __init__(self, data: dict, host: str, peer: str, load_failure: str, duration: str) -> None:
        self.host = host
        self.peer = peer
        self.flow_format = {'direct': f'{self.host} -> {self.peer}',
                            'return': f'{self.peer} <- {self.host}'}
        self.duration = int(duration)
        if not load_failure:
            self.streams = data['start']['test_start']['num_streams']
            self.loss_percent = get_max_lost_percent(data['end']['streams'])
            self.pps_per_stream = int(data['end']['streams'][0]['udp']['packets'] / data['start']['test_start']['duration'])
            self.loss_duration_secs = round(self.duration * self.loss_percent * 0.01, 2)
            self.comment = ''
        else:
            self.streams = 'x'
            self.loss_percent = 'x'
            self.pps_per_stream = 'x'
            self.loss_duration_secs = self.duration
            self.comment = load_failure

    def to_json(self, flow_format='direct'):
        json_format = {
            'flow': self.flow_format[flow_format],
            'duration': self.duration,
            'streams': self.streams,
            'loss_percent': self.loss_percent,
            'pps_per_stream': self.pps_per_stream,
            'loss_duration_secs': self.loss_duration_secs,
            'comment': self.comment
        }
        return json_format


def get_result(data: dict) -> str:
    header = data[0].keys()
    rows = [x.values() for x in data]
    r = tabulate(rows, header, tablefmt='grid')
    return r


def load_json_data(setup_name: str, dir_name: str, host: str, peer: str) -> dict:
    filename = f'../tests/{setup_name}/{dir_name}/client_{host}_server_{peer}.json'
    load_failure = None
    try:
        with open(filename) as f:
            data = json.load(f)
    except FileNotFoundError:
        load_failure = 'file not found'
        print(f'{load_failure}. filename: {filename}.')
        data = None
    except json.decoder.JSONDecodeError:
        load_failure = 'json decode error'
        print(f'{load_failure}. filename: {filename}.')
        data = None
      
    if data is not None and 'error' in data:
        print(f'error key is present in json data. filename: {filename}. value: {data["error"]}')
        load_failure = 'error in json'

    return data, load_failure

def get_max_lost_percent(data: dict) -> int:
    lost_percent = 0
    for stream in data:
        if stream['udp']['lost_percent'] > lost_percent:
            lost_percent = stream['udp']['lost_percent']
    return lost_percent


def load_iperf_data(config: dict, dir_name: str, setup_name: str, duration: str) -> dict:
    iperf_data = {}
    for host in config:
        iperf_data[host] = {}
        for peer in config[host]['peers']:
            data, load_failure = load_json_data(setup_name, dir_name, host, peer)
            iperf_data[host][peer] = Flow(data, host, peer, load_failure, duration)
    return iperf_data


def get_summary_data(data):
    summary_data = []
    flows = []
    for host in data:
        for peer in data[host]:
            if {host, peer} not in flows:
                summary_data.append(data[host][peer].to_json())
                summary_data.append(data[peer][host].to_json(flow_format='return'))
                flows.append({host, peer})
    return summary_data


def main(setup_name, dir_name, duration):
    config = load_config(setup_name)

    data = load_iperf_data(config, dir_name, setup_name, duration)
    # print(json.dumps(data, indent=4))
    summary_data = get_summary_data(data)
    result = get_result(summary_data)
    print(result)
    with open(f'../tests/{setup_name}/{dir_name}/summary.log', 'w') as f:
        f.write(result)
        f.write('\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("setup_name")
    parser.add_argument("dir")
    parser.add_argument("duration")

    args = parser.parse_args()
    main(args.setup_name, args.dir, args.duration)
