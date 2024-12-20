# Apigee Edge KVM decypter
This repository provides scripts and utilities for exporting and decrypting Apigee Key Value Map (KVM) data. It focuses on extracting encrypted KVM values, decrypting them using the correct Key Encryption Key (KEK) and Data Encryption Key (DEK), and outputting the decrypted data in a usable format. The scripts primarily use command-line tools like openssl, awk, xxd, and base64.

Workflow:

* Environment Setup: Set the STOREPASS and VAULT environment variables using the provided awk commands. These variables point to the Apigee credentials and vault location, respectively. These are crucial for accessing the encrypted keys.

*  KEK Extraction: Extract the KEK using the provided Java tool JKSExtractSKE. The command requires the vault path and specific datastore alias, credential utility information as arguments. The output is the KEK required for later decryption steps.

*  DEK Extraction (datastore-alias): The DEK is also extracted using the JKSExtractSKE Java tool using the vault path and a specific datastore alias (e.g. 'datastore-alias', 'CredentialUtil', 'CredentialUtil'). This DEK is encrypted with the KEK.

*  First Layer Decryption (Unlocking the DEK): Decrypt the extracted DEK using the KEK and the openssl command. This decrypted DEK will be used to decrypt the actual KVM values. The example shows decrypting a sample base64 encoded value (AM3ApqDgrhFOCv+bDh85F65QC1MY3HH9eCNXJ08z2aw=) with the extracted KEK using AES-128-ECB decryption. The output is the base64 encoded DEK (oShQOZt8yyxU3+W8spdc/A==).

*  DEK Conversion (base64 to hex): Convert the base64 encoded DEK to its hexadecimal representation using base64 and xxd. This hexadecimal representation of the DEK (a12850399b7ccb2c54dfe5bcb2975cfc in the example) is used in the final decryption step.

*  Second Layer Decryption (Unlocking KVM values): Decrypt the base64 encoded and encrypted KVM values (like "DtdfDdHtxc9W8EI42mpG5A==") using the hexadecimal DEK obtained in the previous step. This uses the same openssl decryption method (AES-128-ECB) with the derived DEK.


# Steps
## Fetch Cassandra STOREPASS &  VAULT location

```
export STOREPASS=$(awk -F= '/^vault.passphrase/{FS="=";print($2)}' /opt/apigee/edge-management-server/conf/credentials.properties)
export VAULT=$(awk -F= '/^vault.filepath/{FS="=";print($2)}' /opt/apigee/edge-management-server/conf/credentials.properties)
```

# Fetch KEK using the Java Code

Compile the Java Code

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