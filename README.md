# Apigee Edge KVM decypter
This repository provides scripts and utilities for exporting and decrypting Apigee Key Value Map (KVM) data. It focuses on extracting encrypted KVM values, decrypting them using the correct Key Encryption Key (KEK) and Data Encryption Key (DEK), and outputting the decrypted data in a usable format. The scripts primarily use command-line tools like python, openssl, awk, xxd, and base64.

# Steps

## Fetch Cassandra vault location  & storepass

Run the below command on the OPDK management server.

```
export STOREPASS=$(awk -F= '/^vault.passphrase/{FS="=";print($2)}' /opt/apigee/edge-management-server/conf/credentials.properties)
export VAULT=$(awk -F= '/^vault.filepath/{FS="=";print($2)}' /opt/apigee/edge-management-server/conf/credentials.properties)
```

# Fetch KEK using the Java Code

Compile the Java Code.  `opdk/JKSExtractSKE.java`

```
javac JKSExtractSKE.java
```

Run the Java code

```
java JKSExtractSKE $VAULT datastore-alias $STOREPASS $STOREPASS
```

Eg.
```
java JKSExtractSKE /opt/apigee/edge-gateway/vault/com.apigee.datastore.util.datastore.vault datastore-alias xxx xxx
14dadc9f2e3e0d3cc774f07f5a0357f1
```

# Run the Script

```
python3 main.py --org <apigee_org_name> --cass_ip <cassandra_ip> --kek <kek>

```

Eg.
```
python3 main.py --org validate --cass_ip 10.0.0.4 --kek 14dadc9f2e3e0d3cc774f07f5a0357f1
```