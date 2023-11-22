# lazyconn

A python tool that allows you to lazily connect to an EC2 instance

## Installation

**Requirements**: [Python 3](https://www.python.org/downloads/release/python-3113/) | [AWS CLI](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html)

If you just installed the AWS CLI, then run the following command:
```bash
aws configure
# enter aws access key id, secret access key, default region (optional). (default output format does not need to be configured)
```

Cloning the repo & Installing dependencies:
```bash
git clone https://github.com/brokerage-systems/lazyconn.git
cd lazyconn/
pip install -r requirements.txt
```

## Usage

```python
python lazyconn.py --help
```

**Specifying a region:**
lazyconn will automatically use the aws cli configured region and if that isn't configured **and** no region parameter is passed, it will default to us-east-1!
```python
python lazyconn.py -r us-west-2
```

**Specifying a user:**
if nothing is specified, there will be a prompt to enter the username
```python
python lazyconn.py -u ec2-user
```

### Getting even lazier!
**Creating a config: (~/.ssh/lazyconn.json)**
lazyconn will read this config, loop through all available instances, match the name, then use the configured options to connect to the instance.
```json
{
    "match": {
        "name": [
            {
                "contains": "ECS",
                "user": "ec2-user"
            },
            {
                "contains": "App",
                "user": "ubuntu"
            }
        ]
    }
}
```

#### Match Example

**Instance List:**
```txt
┌─────┬─────────────────────┬────────────────────────┬──────────────────────────┬────────────────┬─────────┐
│   # │ ID                  │ Name                   │ Type                     │ IP Address     │ Key     │
├─────┼─────────────────────┼────────────────────────┼──────────────────────────┼────────────────┼─────────┤
│  1  │ i-01111111111111111 │ ECS Instance - Website │ (Linux/UNIX) t2.medium   │ 123.24.25.250  │ ecs.pem │
├─────┼─────────────────────┼────────────────────────┼──────────────────────────┼────────────────┼─────────┤
│  2  │ i-02222222222222222 │ App Server             │ (Linux/UNIX) t3.medium   │ 124.25.26.251  │ ec2.pem │
└─────┴─────────────────────┴────────────────────────┴──────────────────────────┴────────────────┴─────────┘
```

**Pattern example #1**
This will connect to the "ECS Instance - Website" instance with the user "ec2-user" automatically.
```python
python lazyconn.py -m "Website"
```
**Pattern example #2**
This will connect to the "App Server" instance with the user "ubuntu" automatically.
```python
python lazyconn.py -m "App"
```