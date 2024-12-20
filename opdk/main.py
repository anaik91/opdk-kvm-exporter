import argparse
import subprocess
import json
import sys

def print_json(data):
    print(json.dumps(data, indent=2))

def load_json(data):
    return json.loads(data)

def write_json(file, data):
    try:
        print(f"Writing JSON to File {file}")
        with open(file, 'w') as fl:
            fl.write(json.dumps(data, indent=2))
    except FileNotFoundError:
        print(f"File \"{file}\" not found")
        return False
    return True

def write_file(file_path, data):
    try:
        with open(file_path, "w") as f:
            f.write(data)
    except Exception as e:
        print(f"Couldn't read file {file_path}. ERROR-INFO- {e}")

def run_command(command):
    try:
        # Execute the command using subprocess.run()
        process = subprocess.run(
            command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False  # Don't raise exception on non-zero exit codes
        )
        return process.returncode, process.stdout, process.stderr
    except FileNotFoundError:
        return -1, "", f"Command not found: {command}"
    except Exception as e:
        return -1, "", f"An error occurred: {e}"

def export_raw_kvm_data(org, cassandra_ip):
    cassandra_cli = '/opt/apigee/apigee-cassandra/bin/cassandra-cli'
    cmd = f'echo -e "use keyvaluemap;\\nget keyvaluemaps_r21[{org}];" | {cassandra_cli} -h {cassandra_ip}'
    returncode, stdout, stderr = run_command(cmd)
    if returncode == 0:
        return stdout
    else:
        print(f"Command failed with error code {returncode}: {stderr}")
        return ''
    # return open('/Users/ashwinknaik/codes/python/opdk-kvm-exporter/cass-cli/output.txt','rb').read()

def get_kvm_scope(kvm_scope_identifier):
    if kvm_scope_identifier == '=> (name=':
        return 'org',''
    scope_split = kvm_scope_identifier.split(":")
    scope = scope_split[0].split("s@")[1]
    if scope == 'apis':
        api_name = scope_split[1].split("s@")[1]
        if 's@revision:s@' in kvm_scope_identifier:
            api_name = scope_split[1].split("s@")[1]
            rev = scope_split[3].split("s@")[1]
            scope = 'rev'
            scope_name=f"{api_name}:{rev}"
        else:
            scope_name=api_name
    else:
        scope_name = scope_split[1].split("s@")[1]
    return scope, scope_name

def decrypt_aes_128_ecb(data, key):
    process = subprocess.Popen(
        ['openssl', 'enc', '-aes-128-ecb', '-d', '-K', key, '-base64', '-A'],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    stdout, stderr = process.communicate(input=data.encode())
    return stdout.decode()

def base64_to_hex(data):
    cmd = f"echo {data}| base64 -d | xxd -ps"
    returncode, stdout, stderr = run_command(cmd)
    if returncode == 0:
        return stdout
    else:
        return f'Failed hex conversion. Error: {stderr}'

def decrypt_kvm_value(kek, dekb64, data):
    dek = decrypt_aes_128_ecb(dekb64.strip(), kek.strip())
    dekhex = base64_to_hex(dek.strip())
    value = decrypt_aes_128_ecb(data.strip(), dekhex.strip())
    return value

def get_kvm_data(kvm_data):
    kvm_name = kvm_data.split(",")[0]
    kvm_value = load_json(kvm_data.split("value=")[1].split(', timestamp=')[0])
    return kvm_name, kvm_value

def key_exists_ignore_case(json_data, key):
    """Checks if a key exists in a JSON object, ignoring case."""
    lower_key = key.lower()
    for k in json_data.keys():
        if k.lower() == lower_key:
            return json_data[k]
    return ''

def get_decrypted_kvm_data(kvm_key, kvm_data, kek, dekb64):
    kvm_value = []
    kvm_data = key_exists_ignore_case(kvm_data, kvm_key)
    for each_value in load_json(kvm_data):
        kvm_value.append({
            'name': each_value.get('name'),
            'value': decrypt_kvm_value(kek, dekb64, each_value.get('value'))
        })
    return kvm_value

def process_raw_kvm(kvm_data, org, kek):
    kvms = kvm_data.splitlines()
    filtered_kvms = [ line for line in kvms if line.startswith('=>') ]
    kvm_json = {
        'org':{},
        'env':{},
        'apis':{},
        'rev':{}
    }
    # populate
    for each_line in filtered_kvms:
        each_line_tuple = each_line.split("s@kvmaps:s@")
        kvm_scope, kvm_scope_name = get_kvm_scope(each_line_tuple[0])
        kvm_name, kvm_value  = get_kvm_data(each_line_tuple[1])
        if kvm_scope_name in kvm_json[kvm_scope]:
            kvm_json[kvm_scope][kvm_scope_name][kvm_name]=kvm_value
        else:
            kvm_json[kvm_scope][kvm_scope_name]={}
            kvm_json[kvm_scope][kvm_scope_name][kvm_name]=kvm_value
        # print(f"kvm_name: {kvm_name} | kvm_scope: {kvm_scope} | kvm_scope_name: {kvm_scope_name}")
    write_json('kvms.json', kvm_json)
    kvm_json_decrypted = {
        'org':{},
        'env':{},
        'apis':{},
        'rev':{}
    }
    # decrypt
    for scope, scope_data in kvm_json.items():
        for each_scope, each_scope_data in scope_data.items():
            dekb64 = load_json(each_scope_data.get('__ apigee__kvm__.keystore').get('__ apigee__kvm__.keystore'))[0].get('value','')
            for each_kvm, each_kvm_value in each_scope_data.items():
                if each_kvm != '__ apigee__kvm__.keystore':
                    kvm_encrypted = each_kvm_value.get('__apigee__encrypted', 'false')
                    if kvm_encrypted == 'true':
                        dec_kvm_value = get_decrypted_kvm_data(each_kvm, each_kvm_value, kek, dekb64)
                        if each_scope in kvm_json_decrypted[scope]:
                            kvm_json_decrypted[scope][each_scope][each_kvm]=dec_kvm_value
                        else:
                            kvm_json_decrypted[scope][each_scope]={}
                            kvm_json_decrypted[scope][each_scope][each_kvm]=dec_kvm_value
                    else:
                        dict_kvm_value= load_json(each_kvm_value.get(each_kvm)) if each_kvm_value.get(each_kvm) is not None else {}
                        if each_scope in kvm_json_decrypted[scope]:
                            kvm_json_decrypted[scope][each_scope][each_kvm]=dict_kvm_value
                        else:
                            kvm_json_decrypted[scope][each_scope]={}
                            kvm_json_decrypted[scope][each_scope][each_kvm]=dict_kvm_value
    if '' in kvm_json_decrypted['org']:
        kvm_json_decrypted['org'][org]=kvm_json_decrypted['org']['']
        kvm_json_decrypted['org'].pop('')
    write_json('kvms_decrypted.json', kvm_json_decrypted)

# Example usage:
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Apigee OPDK KVM Exporter')
    parser.add_argument('--org', type=str, help="Apigee org name")
    parser.add_argument('--cass_ip', type=str, help="Apigee cassandra ip")
    parser.add_argument('--kek', type=str, help="Apigee KEK")
    args = parser.parse_args()
    raw_kvm_data = export_raw_kvm_data(args.org, args.cass_ip)
    process_raw_kvm(raw_kvm_data.decode('utf-8'), args.org, args.kek)
