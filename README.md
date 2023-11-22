# lazyconn

A python tool that allows you to lazily connect to any of your AWS EC2 instances!

**Why use lazyconn?**
 1. You won't have to remember IP Addresses.
 2. Faster & easier to connect to instances w/ dynamic IP Addresses.
 3. With a proper lazyconn config, you won't have to remember usernames.
 4. You won't have to remember which key files go to which instances.
 5. Nice TUI that shows you what you need to know about an instance before connecting.
 6. Allows you to easily bounce between instances.

## Installation With Docker

**Requirements**: [Docker](https://www.docker.com/get-started/)

Cloning the repo:
```bash
git clone https://github.com/brokerage-systems/lazyconn.git
cd lazyconn/
```

Building with Docker
```bash
docker build --build-arg AWS_ACCESS_KEY_ID=XXXXXXXXXXXXXXXXXXXX --build-arg AWS_SECRET_ACCESS_KEY=XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX -t lazyconn .
```

## Example Usage With Docker

**Note:** We attach a docker volume to our .ssh/ directory so lazyconn can read our key files & lazyconn config!
```bash
docker run -i --rm -v /home/josh/.ssh/:/root/.ssh/ lazyconn --help
```

**Specifying a region:**
lazyconn will automatically use the aws cli configured region and if that isn't configured **and** no region parameter is passed, it will default to us-east-1!
```bash
docker run -i --rm -v /home/josh/.ssh/:/root/.ssh/ lazyconn -r us-east-1
```

**Specifying a user:**
if nothing is specified, there will be a prompt to enter the username
```bash
docker run -i --rm -v /home/josh/.ssh/:/root/.ssh/ lazyconn -u ec2-user
```

---

### Installation Without Docker

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

---

### Example Usage Without Docker

```bash
python3 lazyconn.py --help
```

**Specifying a region:**
lazyconn will automatically use the aws cli configured region and if that isn't configured **and** no region parameter is passed, it will default to us-east-1!
```bash
python3 lazyconn.py -r us-west-2
```

**Specifying a user:**
if nothing is specified, there will be a prompt to enter the username
```bash
python3 lazyconn.py -u ec2-user
```

## Getting even lazier!
**Create a config file @ ~/.ssh/lazyconn.json**
then lazyconn will read this config, loop through all available instances, match the name, then use the configured options to connect to the instance.
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

---

### Match Example

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

---

**Pattern example #1**
This will connect to the "ECS Instance - Website" instance with the user "ec2-user" automatically.
```bash
python3 lazyconn.py -m "Website"
```
or
```bash
docker run -i --rm -v /home/josh/.ssh/:/root/.ssh/ lazyconn -m "Website"
```

---

**Pattern example #2**
This will connect to the "App Server" instance with the user "ubuntu" automatically.
```bash
python3 lazyconn.py -m "App"
```
or
```bash
docker run -i --rm -v /home/josh/.ssh/:/root/.ssh/ lazyconn -m "App"
```