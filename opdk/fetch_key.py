import jks
import sys
import binascii

def main():
    """
    Extracts a secret key from a JCEKS keystore and prints it as a hex string.
    """
    if len(sys.argv) < 5:
        print("ERROR: python extract_key.py <vault> <alias> <storepass> <keypass>")
        sys.exit(1)

    file_name = sys.argv[1]
    alias = sys.argv[2]
    store_pass = sys.argv[3]
    key_pass = sys.argv[4]

    try:
        # Load the keystore
        ks = jks.KeyStore.load(file_name, store_pass)

        # Check if the alias exists in secret_keys
        if alias not in ks.secret_keys:
            # If not in secret_keys, try to decrypt it from private_keys with the key_pass
            if alias in ks.private_keys:
                 pk_entry = ks.private_keys[alias]
                 if not pk_entry.is_decrypted():
                     pk_entry.decrypt(key_pass)
                 # The 'key' attribute holds the raw secret key for secret key entries
                 # stored as private key entries
                 secret_key = pk_entry.key
            else:
                 print(f"ERROR: Alias '{alias}' not found in the keystore.")
                 sys.exit(1)
        else:
            # If the entry is in secret_keys, it's already decrypted
            sk_entry = ks.secret_keys[alias]
            secret_key = sk_entry.key


        # Convert the key to a hexadecimal string and print
        print(binascii.hexlify(secret_key).decode('utf-8'))

    except jks.util.KeystoreSignatureException:
        print("ERROR: Invalid keystore password or integrity check failed.")
        sys.exit(1)
    except Exception as e:
        print(f"An error occurred: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
