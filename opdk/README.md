# Apigee opdk KVM decypter

Below is the usage of the script. This script has to be run from cassandra server.

```
python3 main.py --help
usage: main.py [-h] [--org ORG] [--cass_ip CASS_IP] [--kek KEK] [--raw_export] [--raw_import] [--apigeecli_export] [--mvncli_export]
               [--mvncli_export_expand]

Apigee OPDK KVM Exporter

options:
  -h, --help            show this help message and exit
  --org ORG             Apigee org name
  --cass_ip CASS_IP     Apigee cassandra ip
  --kek KEK             Apigee KEK
  --raw_export          Generate raw kvm data export using cassandra-cli
  --raw_import          Decrypt kvm data from raw export
  --apigeecli_export    Flag to export kvm data into apigeecli format
  --mvncli_export       Flag to export kvm data into mvn cli format into a single file
  --mvncli_export_expand
                        Flag to export kvm data into mvn cli format into a multiple files
```

## Example of decrypt of kvms

```
python3 main.py \
  --org validate \
  --cass_ip 10.0.0.4 
  --kek 14dadc9f2e3e0d3cc774f07f5a0357f1
```


## Example of raw export of kvms using cassandra-cli [No kvm decrypt]

```
python3 main.py \
  --org validate \
  --cass_ip 10.0.0.4 
  --kek 14dadc9f2e3e0d3cc774f07f5a0357f1
```

## Example of raw import of export of cassandra-cli to decrypt kvms

```
python3 main.py \
  --org validate \
  --cass_ip 10.0.0.4 
  --kek 14dadc9f2e3e0d3cc774f07f5a0357f1
```

## Example with apigeecli format export

```
python3 main.py \
  --org validate \
  --cass_ip 10.0.0.4 
  --kek 14dadc9f2e3e0d3cc774f07f5a0357f1 \
  --apigeecli_export
```

## Example with maven plugin format export into single file

```
python3 main.py \
  --org validate \
  --cass_ip 10.0.0.4 
  --kek 14dadc9f2e3e0d3cc774f07f5a0357f1 \
  --mvncli_export
```


## Example with maven plugin format export into multiple files

```
python3 main.py \
  --org validate \
  --cass_ip 10.0.0.4 
  --kek 14dadc9f2e3e0d3cc774f07f5a0357f1 \
  --mvncli_export \
  --mvncli_export_expand
```