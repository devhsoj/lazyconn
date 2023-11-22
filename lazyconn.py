from tabulate import tabulate
import subprocess
import argparse
import os.path
import json
import sys


def load_config():
    config = None
    config_path = os.path.expanduser(f'~/.ssh/lazyconn.json')

    if os.path.isfile(config_path):
        cf = open(config_path, 'r')
        config = json.loads(cf.read())
        cf.close()

    return config


def get_cli_command_output(args, env=None, quiet=False):
    result = subprocess.run(args, capture_output=True, env=env)

    if result.returncode != 0:
        if not quiet:
            print(f'aws cli command failed to run: "{result.stderr}"')
            sys.exit(result.returncode)

    return result.stdout.decode('utf-8')


def get_aws_cli_version():
    output = get_cli_command_output(['aws', '--version']).strip()

    metadata = output.split(' ')
    version_metadata = metadata[0].split('/')
    version_number_metadata = version_metadata[1].split('.')

    return {
        'major': float(version_number_metadata[0]),
        'minor': float(version_number_metadata[1]),
        'patch': float(version_number_metadata[2]),
    }


def get_instance_data(region):
    aws_cli_region = get_cli_command_output(['aws', 'configure', 'get', 'region'], quiet=True).strip()

    if region is None:
        if aws_cli_region == 'None' or aws_cli_region == '':
            region = 'us-east-1'
        else:
            region = aws_cli_region

    aws_cli_version = get_aws_cli_version()

    aws_cli_ec2_args = ['aws', 'ec2', 'describe-instances', '--output', 'json', '--region', region]
    aws_cli_ec2_env = os.environ.copy()

    aws_cli_ec2_env['AWS_PAGER'] = ''

    if aws_cli_version['major'] == 2:
        aws_cli_ec2_args.append('--no-cli-pager')

    aws_cli_ec2_output = get_cli_command_output(aws_cli_ec2_args, env=aws_cli_ec2_env)
    instance_data = json.loads(aws_cli_ec2_output)

    return instance_data


def get_available_instances(instance_data):
    available_instances = []

    for instance_batch in instance_data['Reservations']:
        for i in range(0, len(instance_batch['Instances'])):
            instance = instance_batch['Instances'][i]

            if instance['State']['Code'] != 80 and 'PublicIpAddress' in instance:
                tags = instance['Tags']
                nameTags = [tag for tag in tags if tag['Key'] == 'Name']

                available_instances.append([
                    i + 1,
                    instance['InstanceId'],
                    nameTags[0]['Value'] or 'N/A',
                    f'({instance["PlatformDetails"]}) {instance["InstanceType"]}',
                    instance['PublicIpAddress'],
                    instance['KeyName'] + '.pem'
                ])

    return available_instances


def match_instance(formatted_instances, pattern, config):
    instance = None
    user = None

    for instance_ in formatted_instances:
        if pattern != None:
            if pattern in instance_[2] or pattern == instance_[2]:
                if config != None:
                    if 'match' in config:
                        if 'name' in config['match']:
                            for name_match in config['match']['name']:
                                if name_match['contains'] in instance_[2]:
                                    user = name_match['user']

                                    if pattern in instance_[2]:
                                        instance = instance_
                                        break

                instance = instance_

    return (instance, user)


def main():
    parser = argparse.ArgumentParser(prog='lazyconn', description='Connect to any AWS EC2 instance with ease!')

    parser.add_argument('-r', '--region', help='AWS region to read instances from', default=None)
    parser.add_argument('-u', '--user', help='Default user to connect as', default=None)
    parser.add_argument('-m', '--match', help='Matches the EC2 instance name to connection options specified in ~/.ssh/lazyconn.json', default=None)

    args = parser.parse_args()

    instance_data = get_instance_data(args.region)
    available_instances = get_available_instances(instance_data)
    
    if len(available_instances) == 0:
        print(f'error: no available instances!')
        sys.exit(1)

    config = load_config()
    running = True

    while running:
        instance, user = None, None

        if args.match != None:
            instance, user = match_instance(available_instances, args.match, config)

        if args.match == None or instance == None:
            print(tabulate(available_instances, ['#', 'ID', 'Name', 'Type', 'IP Address', 'Key'], tablefmt="simple_grid"))

        while not instance:
            try:
                choice = input(f'\r\nselect instance (#1-#{len(available_instances)})> ')
                index = int(choice.replace('#', '')) - 1

                if index < 0 or index > len(available_instances):
                    raise IndexError

                instance = available_instances[index]
            except (ValueError, IndexError):
                print(f'error: \'{choice}\' is an invalid choice!')
                choice = None

        user = user or args.user or input('user> ')
        key_path = os.path.expanduser(f'~/.ssh/{instance[5]}')

        if not os.path.isfile(key_path):
            print(f'error: key file {instance[5]} not found in ~/.ssh/')
            sys.exit(1)

        ssh_result = subprocess.run(['ssh', '-i', key_path, f'{user}@{instance[4]}'])

        if args.match != None:
            running = False

        if ssh_result.returncode not in [0, 130]:
            print(f'error: ssh failed: "{ssh_result.stdout}"')
            sys.exit(ssh_result.returncode)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('exiting...')
        sys.exit(1)