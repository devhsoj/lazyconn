from tabulate import tabulate
import subprocess
import argparse
import os.path
import json
import sys


def get_lazyconn_config() -> (dict | None):

    '''
    Tries to read ~/.ssh/lazyconn.json, if the file exists, returns a dict from JSON parsing.
    If not, returns None.
    '''

    config = None
    config_path = os.path.expanduser(f'~/.ssh/lazyconn.json')

    if os.path.isfile(config_path):
        cf = open(config_path, 'r')
        config = json.loads(cf.read())
        cf.close()

    return config


def get_cli_command_output(args: list[str], env=None, quiet=False):

    '''
    Helper method for getting the utf-8 decoded output of a shell command.
    '''

    result = subprocess.run(args, capture_output=True, env=env)

    if result.returncode != 0:
        if not quiet:
            print(f'command failed to run: "{result.stderr}"')
            sys.exit(result.returncode)

    return result.stdout.decode('utf-8')


def get_aws_cli_version():

    '''
    Returns a dictionary holding metadata of the installed AWS CLI version.
    '''

    output = get_cli_command_output(['aws', '--version']).strip()

    metadata = output.split(' ')
    version_metadata = metadata[0].split('/')
    version_number_metadata = version_metadata[1].split('.')

    return {
        'major': float(version_number_metadata[0]),
        'minor': float(version_number_metadata[1]),
        'patch': float(version_number_metadata[2]),
    }


def get_best_region(given_region: str | None):

    '''
    Returns the best region based on what is given and what the AWS CLI has configured.
    '''

    aws_cli_region = get_cli_command_output(['aws', 'configure', 'get', 'region'], quiet=True).strip()

    if given_region is None:
        if aws_cli_region == 'None' or aws_cli_region == '':
            given_region = 'us-east-1'
        else:
            given_region = aws_cli_region

    return given_region


def get_instance_data(region: str):

    '''
    Returns JSON parsed AWS EC2 instance data from the AWS CLI.
    '''

    aws_cli_version = get_aws_cli_version()

    aws_cli_ec2_args = ['aws', 'ec2', 'describe-instances', '--output', 'json', '--region', region]
    aws_cli_ec2_env = os.environ.copy()

    # disable output paging in older AWS CLI versions
    aws_cli_ec2_env['AWS_PAGER'] = ''

    # this parameter only exists in the AWS CLI V2
    if aws_cli_version['major'] == 2:
        aws_cli_ec2_args.append('--no-cli-pager')

    aws_cli_ec2_output = get_cli_command_output(aws_cli_ec2_args, env=aws_cli_ec2_env)
    instance_data = json.loads(aws_cli_ec2_output)

    return instance_data


def get_running_instances(instance_data):

    '''
    Returns list of all running instances evaluated from instance_data.
    '''

    running_instances = []

    for instance_batch in instance_data['Reservations']:
        for i in range(0, len(instance_batch['Instances'])):
            instance = instance_batch['Instances'][i]

            # 16 = running
            if instance['State']['Code'] == 16 and 'PublicIpAddress' in instance:
                running_instances.append(instance)

    return running_instances


def match_instance_name_to_config(formatted_instances, pattern: str, config: dict):

    '''
    Tries to match a string pattern to the name of each instance in formatted_instances, if
    a match is found, then return the configured user along with the matched instance.
    '''

    instance = None
    user = None

    for instance_ in formatted_instances:
        if pattern != None:
            tags = instance_['Tags']
            name_tags = [tag for tag in tags if tag['Key'] == 'Name']

            instance_name = name_tags[0]['Value'] or ''

            if instance_name and (pattern in instance_name or pattern == instance_name):
                if config != None:
                    if 'match' in config:
                        if 'name' in config['match']:
                            for name_match in config['match']['name']:
                                if name_match['contains'] in instance_name:
                                    user = name_match['user']

                                    if pattern in instance_name:
                                        instance = instance_
                                        break

                instance = instance_

    return (instance, user)


def tabulate_running_instance_data(running_instances: list):

    '''
    Returns a list of instances in a tabulated data format for the package tabulate.
    '''

    table_data = []

    for i in range(0, len(running_instances)):
        instance = running_instances[i]

        tags = instance['Tags']
        name_tags = [tag for tag in tags if tag['Key'] == 'Name']

        table_data.append([
            i + 1,
            instance['InstanceId'],
            name_tags[0]['Value'] or 'N/A',
            f'({instance["PlatformDetails"]}) {instance["InstanceType"]}',
            instance['PublicIpAddress'],
            instance['KeyName'] + '.pem'
        ])

    return table_data


def main():
    parser = argparse.ArgumentParser(prog='lazyconn', description='A tool that allows you to lazily connect to any of your AWS EC2 instances! ')

    parser.add_argument('-r', '--region', help='AWS region to read instances from.', default=None)
    parser.add_argument('-u', '--user', help='Default user to login as.', default=None)
    parser.add_argument('-m', '--match', help='Pattern to match an EC2 instance name against to connection options specified in ~/.ssh/lazyconn.json.', default=None)

    args = parser.parse_args()

    region = get_best_region(args.region)
    instance_data = get_instance_data(region)
    running_instances = get_running_instances(instance_data)
    
    if len(running_instances) == 0:
        print(f'error: no running instances found in {region}!')
        sys.exit(1)

    config = get_lazyconn_config()
    running = True

    while running:
        instance, user = None, None

        if args.match != None:
            instance, user = match_instance_name_to_config(running_instances, args.match, config)

        if args.match == None or instance == None:
            print(tabulate(tabulate_running_instance_data(running_instances), ['#', 'ID', 'Name', 'Type', 'IP Address', 'Key'], tablefmt="simple_grid"))

        while not instance:
            try:
                choice = input(f'\r\nselect instance (#1-#{len(running_instances)})> ')
                index = int(choice.replace('#', '')) - 1

                if index < 0 or index > len(running_instances):
                    raise IndexError

                instance = running_instances[index]
            except (ValueError, IndexError):
                print(f'error: "{choice}" is an invalid choice!')
                choice = None

        user = (user or args.user or input('user> ')).strip()
        key_path = os.path.expanduser(f'~/.ssh/{instance["KeyName"]}.pem')

        if not os.path.isfile(key_path):
            print(f'error: key file "{instance["KeyName"]}.pem" not found in ~/.ssh/')
            sys.exit(1)

        ssh_args = ['ssh', '-i', key_path, f'{user}@{instance["PublicIpAddress"]}']

        '''
        if running from a Docker container:
            - force tty allocation
            - disable StrictHostKeyChecking
            - ignore host config files (could be attached via docker volume)
        '''

        if os.getenv('IS_CONTAINER') == 'true':
            ssh_args.extend([
                '-tt',
                '-o',
                'StrictHostKeyChecking=no',
                '-F',
                'none'
            ])

        ssh_result = subprocess.run(ssh_args)

        # if the ssh process has ended and we specified a match parameter, then stop execution
        if args.match != None:
            running = False

        if ssh_result.returncode not in [0, 130]:
            print(f'error: ssh failed: "{ssh_result.stdout}"')
            sys.exit(ssh_result.returncode)


if __name__ == '__main__':
    try:
        main()
    except (KeyboardInterrupt, EOFError):
        print('exiting...')
        sys.exit(1)
