import argparse
import subprocess
import json
import sys
import os

def create_dir(dir):
    try:
        os.makedirs(dir)
    except FileExistsError:
        print(f"Directory \"{dir}\" already exists")

def print_json(data):
    print(json.dumps(data, indent=2))

def load_json(data):
    parsed_data = {}
    try:
        parsed_data = json.loads(data)
    except json.decoder.JSONDecodeError:
        return parsed_data, False
    return parsed_data, True

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
        with open(file_path, "wb") as f:
            f.write(data)
    except Exception as e:
        print(f"Couldn't read file {file_path}. ERROR-INFO- {e}")

def read_file(file_path):
    try:
        with open(file_path, "r") as f:
            content = f.read()
        return content
    except Exception as e:
        print(f"Couldn't read file {file_path}. ERROR-INFO- {e}")
        sys.exit(1)

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
    kvm_value, valid_json = load_json(kvm_data.split("value=")[1].split(', timestamp=')[0])
    if not valid_json:
        kvm_value = {'status': 'JSON decode of kvm entry value failed', kvm_name : kvm_data}
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
    kvm_data_dict, valid_json = load_json(kvm_data)
    for each_value in kvm_data_dict:
        kvm_value.append({
            'name': each_value.get('name'),
            'value': decrypt_kvm_value(kek, dekb64, each_value.get('value'))
        })
    return kvm_value

def apigee_cli_export(kvm_data, export_dir='apigeecli_export'):
    create_dir(export_dir)
    delimiter='__'
    for scope, scope_data in kvm_data.items():
        for each_scope, each_scope_data in scope_data.items():
            for each_kvm, each_kvm_value in each_scope_data.items():
                if isinstance(each_kvm_value, list):
                    kvm_entries = {'keyValueEntries': each_kvm_value }
                else:
                    kvm_entries = {'keyValueEntries': [] }
                if scope == 'org':
                    kvm_file = f'org{delimiter}{each_kvm}{delimiter}kvmfile__0.json'
                    write_json(f'{export_dir}/{kvm_file}', kvm_entries)
                elif scope == 'env':
                    kvm_file = f'env{delimiter}{each_scope}{delimiter}{each_kvm}{delimiter}kvmfile__0.json'
                    write_json(f'{export_dir}/{kvm_file}', kvm_entries)
                elif scope == 'apis':
                    kvm_file = f'proxy{delimiter}{each_scope}{delimiter}{each_kvm}{delimiter}kvmfile__0.json'
                    write_json(f'{export_dir}/{kvm_file}', kvm_entries)
                elif scope == 'rev':
                    kvm_file = f'org{delimiter}{each_kvm}{delimiter}kvmfile__0.json'
                    write_json(f'{export_dir}/{kvm_file}', kvm_entries)
                else:
                    print('Unknown Scope')

def mvn_cli_export(kvm_data, expand, export_dir='mvncli_export'):
    edge_dir = f'{export_dir}/edge'
    create_dir(edge_dir)
    mvn_json = {
        'version': '1.0',
        'envConfig': {},
        'orgConfig' : {
            'kvms': []
        },
        'apiConfig' :{
            'kvms': []
        },
    }
    for scope, scope_data in kvm_data.items():
        for each_scope, each_scope_data in scope_data.items():
            for each_kvm, each_kvm_value in each_scope_data.items():
                if isinstance(each_kvm_value, list):
                    kvm_entries = {'entry': each_kvm_value, 'name': each_kvm }
                else:
                    kvm_entries = {'entry': [], 'name': each_kvm }
                if scope == 'org':
                    mvn_json['orgConfig']['kvms'].append(kvm_entries)
                elif scope == 'env':
                    if each_scope in mvn_json['envConfig']:
                        mvn_json['envConfig'][each_scope]['kvms'].append(kvm_entries)
                    else:
                        mvn_json['envConfig'][each_scope] = { 'kvms': []}
                        mvn_json['envConfig'][each_scope]['kvms'].append(kvm_entries)
                elif scope == 'apis':
                    mvn_json['apiConfig']['kvms'].append(kvm_entries)
                elif scope == 'rev':
                    mvn_json['apiConfig']['kvms'].append(kvm_entries)
                else:
                    print('Unknown Scope')
    if expand:
        create_dir(f'{edge_dir}/org')
        create_dir(f'{edge_dir}/api')
        write_json(f'{edge_dir}/org/kvms.json', mvn_json.get('orgConfig').get('kvms'))
        write_json(f'{edge_dir}/api/kvms.json', mvn_json.get('apiConfig').get('kvms'))
        for env in mvn_json.get('envConfig'):
            create_dir(f'{edge_dir}/env/{env}')
            write_json(f'{edge_dir}/env/{env}/kvms.json', mvn_json.get('envConfig').get(env).get('kvms'))
    else:
        write_json(f'{edge_dir}/edge.json', mvn_json)

def process_raw_kvm(kvm_data, org, kek):
    kvms = kvm_data.splitlines()
    filtered_kvms = [ line for line in kvms if line.startswith('=>') ]
    kvm_json = {
        'org': {},
        'env': {},
        'apis': {},
        'rev': {}
    }
    # populate
    for each_line in filtered_kvms:
        each_line_tuple = each_line.split("s@kvmaps:s@")
        kvm_scope, kvm_scope_name = get_kvm_scope(each_line_tuple[0])
        kvm_name, kvm_value  = get_kvm_data(each_line_tuple[1])
        if kvm_scope_name in kvm_json[kvm_scope]:
            kvm_json[kvm_scope][kvm_scope_name][kvm_name]=kvm_value
        else:
            kvm_json[kvm_scope][kvm_scope_name] = {}
            kvm_json[kvm_scope][kvm_scope_name][kvm_name]=kvm_value
        # print(f"kvm_name: {kvm_name} | kvm_scope: {kvm_scope} | kvm_scope_name: {kvm_scope_name}")
    write_json('kvms.json', kvm_json)
    kvm_json_decrypted = {
        'org': {},
        'env': {},
        'apis': {},
        'rev': {}
    }
    # decrypt
    for scope, scope_data in kvm_json.items():
        for each_scope, each_scope_data in scope_data.items():
            enc_keystore=each_scope_data.get('__ apigee__kvm__.keystore')
            if enc_keystore is None:
                continue
            enc_keystore_child, _ = load_json(enc_keystore.get('__ apigee__kvm__.keystore'))
            dekb64 = enc_keystore_child[0].get('value','')
            for each_kvm, each_kvm_value in each_scope_data.items():
                if each_kvm != '__ apigee__kvm__.keystore':
                    kvm_encrypted = each_kvm_value.get('__apigee__encrypted', 'false')
                    if kvm_encrypted == 'true':
                        dec_kvm_value = get_decrypted_kvm_data(each_kvm, each_kvm_value, kek, dekb64)
                        if each_scope in kvm_json_decrypted[scope]:
                            kvm_json_decrypted[scope][each_scope][each_kvm]=dec_kvm_value
                        else:
                            kvm_json_decrypted[scope][each_scope] = {}
                            kvm_json_decrypted[scope][each_scope][each_kvm]=dec_kvm_value
                    else:
                        if each_kvm_value.get(each_kvm):
                            dict_kvm_value, valid_json = load_json(each_kvm_value.get(each_kvm))
                            if not valid_json:
                                dict_kvm_value = {'value' : each_kvm_value}
                        else:
                            dict_kvm_value = {}
                        if each_scope in kvm_json_decrypted[scope]:
                            kvm_json_decrypted[scope][each_scope][each_kvm] = dict_kvm_value
                        else:
                            kvm_json_decrypted[scope][each_scope] = {}
                            kvm_json_decrypted[scope][each_scope][each_kvm] = dict_kvm_value
    if '' in kvm_json_decrypted['org']:
        kvm_json_decrypted['org'][org]=kvm_json_decrypted['org']['']
        kvm_json_decrypted['org'].pop('')
    write_json('kvms_decrypted.json', kvm_json_decrypted)
    return kvm_json_decrypted

# Example usage:
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Apigee OPDK KVM Exporter')
    parser.add_argument('--org', type=str, help="Apigee org name")
    parser.add_argument('--cass_ip', type=str, help="Apigee cassandra ip")
    parser.add_argument('--kek', type=str, help="Apigee KEK")
    parser.add_argument('--raw_export', help="Generate raw kvm data export using cassandra-cli", action='store_true')
    parser.add_argument('--raw_import', help="Decrypt kvm data from raw export", action='store_true')
    parser.add_argument('--apigeecli_export', help="Flag to export kvm data into apigeecli format", action='store_true')
    parser.add_argument('--mvncli_export', help="Flag to export kvm data into mvn cli format into a single file", action='store_true')
    parser.add_argument('--mvncli_export_expand', help="Flag to export kvm data into mvn cli format into a multiple files", action='store_true')
    args = parser.parse_args()
    raw_kvm_data = ''
    if args.raw_export:
        raw_kvm_data = export_raw_kvm_data(args.org, args.cass_ip)
        write_file('raw_export.txt',raw_kvm_data)
        sys.exit(0)
    kvm_json_decrypted = {}
    if args.raw_import:
        raw_kvm_data=read_file('raw_export.txt')
        kvm_json_decrypted = process_raw_kvm(raw_kvm_data, args.org, args.kek)
    else:
        raw_kvm_data = export_raw_kvm_data(args.org, args.cass_ip)
        kvm_json_decrypted=process_raw_kvm(raw_kvm_data.decode('utf-8'), args.org, args.kek)
    if args.apigeecli_export:
        apigee_cli_export(kvm_json_decrypted)
    if args.mvncli_export:
        if args.mvncli_export_expand:
            mvn_cli_export(kvm_json_decrypted, True)
        else:
            mvn_cli_export(kvm_json_decrypted, False)
