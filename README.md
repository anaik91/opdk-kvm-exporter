# Apigee Edge KVM decypter
This repository provides scripts and utilities for exporting and decrypting Apigee Key Value Map (KVM) data. It focuses on extracting encrypted KVM values, decrypting them using the correct Key Encryption Key (KEK) and Data Encryption Key (DEK), and outputting the decrypted data in a usable format. The scripts primarily use command-line tools like python, openssl, awk, xxd, and base64.

# Steps

## Apigee Edge OPDK

**High Level steps**
1. Fetch Key Encryption Key
    * Fetch OPDK Cassandra Vault Location  & Storepass
    * Compile the provided Java Code [JKSExtractSKE.java](./opdk/JKSExtractSKE.java)
    * Run the compiled Java Code to fetch KEK
2. Run the Python Script [main.py](./opdk/main.py) to export the KVM data

### Fetch Cassandra vault location  & storepass

Run the below command on the OPDK management server.

```bash
export STOREPASS=$(awk -F= '/^vault.passphrase/{FS="=";print($2)}' /opt/apigee/edge-management-server/conf/credentials.properties)
export VAULT=$(awk -F= '/^vault.filepath/{FS="=";print($2)}' /opt/apigee/edge-management-server/conf/credentials.properties)
```

### Fetch KEK using the Java Code

Compile the Java Code.  `opdk/JKSExtractSKE.java`

```bash
javac JKSExtractSKE.java
```

Run the Java code

```bash
java JKSExtractSKE $VAULT datastore-alias $STOREPASS $STOREPASS
```

Eg.
```bash
java JKSExtractSKE /opt/apigee/edge-gateway/vault/com.apigee.datastore.util.datastore.vault datastore-alias xxx xxx
14dadc9f2e3e0d3cc774f07f5a0357f1
```

### Run the Script

```bash
python3 main.py --org <apigee_org_name> --cass_ip <cassandra_ip> --kek <kek>
```

Eg.
```bash
python3 main.py --org validate --cass_ip 10.0.0.4 --kek 14dadc9f2e3e0d3cc774f07f5a0357f1
```

Refer the [readme](./opdk/README.md) for all script options and actions

## Apigee Edge SAAS

TBD