# Apigee opdk KVM decypter

Below is the usage of the script.

```
usage: main.py [-h] [--org ORG] [--cass_ip CASS_IP] [--kek KEK]

Apigee OPDK KVM Exporter

options:
  -h, --help         show this help message and exit
  --org ORG          Apigee org name
  --cass_ip CASS_IP  Apigee cassandra ip
  --kek KEK          Apigee KEK
```

Eg.

```
python3 main.py --org validate --cass_ip 10.0.0.4 --kek 14dadc9f2e3e0d3cc774f07f5a0357f1
```