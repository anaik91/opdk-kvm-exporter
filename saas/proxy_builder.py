import os
import json
import utils
import shutil

def build_kvm_policy(kvm_data):
    kvm_get_arr=[]
    for each_entry in kvm_data.get('entry', []):
        each_entry_name = each_entry.get('name','')
        kvm_get_arr.append(f'''<Get assignTo="private.{each_entry_name}">
            <Key>
                <Parameter>{each_entry_name}</Parameter>
            </Key>
        </Get>''')
    kvm_get_obj='\n'.join(kvm_get_arr)
    kvm_policy=f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
    <KeyValueMapOperations name="get-encrypted" mapIdentifier="{kvm_data.get('name')}">
        <Scope>environment</Scope>
        {kvm_get_obj}
    </KeyValueMapOperations>
    '''
    return kvm_policy

def build_am_policy(kvm_data):
    policy_payload={'name': kvm_data.get('name'), 'entry': []}
    for key in kvm_data.get('entry',[]):
        value_str = "{private." + key.get('name') + "}"
        policy_payload['entry'].append({
        "name": key.get('name'),
        "value": value_str
        })
    am_policy = f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
    <AssignMessage name="set-payload">
        <Set>
            <Payload contentType="application/json">
            {json.dumps(policy_payload,indent=2)}
            </Payload>
        </Set>
    </AssignMessage>'''
    return am_policy

def build_api_proxy_root(proxy_name, proxy_path):
    root_xml=f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<APIProxy revision="1" name="{proxy_name}">
    <Basepaths>{proxy_path}</Basepaths>
    <Description></Description>
    <DisplayName>{proxy_name}</DisplayName>
    <Policies>
        <Policy>get-encrypted</Policy>
        <Policy>set-payload</Policy>
    </Policies>
    <ProxyEndpoints>
        <ProxyEndpoint>default</ProxyEndpoint>
    </ProxyEndpoints>
    <Resources/>
    <Spec></Spec>
    <TargetServers/>
    <TargetEndpoints/>
</APIProxy>
'''
    return root_xml

def prepare_api_proxy(kvm_data, base_dir):
    cwd = os.path.dirname(os.path.abspath(__file__))
    proxy_name = kvm_data.get('name')
    destination_dir = f"{base_dir}/{proxy_name}/apiproxy"
    proxy_path = f"/encrypted_kvm_fetch/{proxy_name}"
    proxy_bundle_dir=os.path.join(cwd,'apiproxy')
    shutil.copytree(proxy_bundle_dir, destination_dir)
    kvm_policy_path=os.path.join(destination_dir, 'policies','get-encrypted.xml')
    am_policy_path=os.path.join(destination_dir, 'policies','set-payload.xml')
    root_proxy_path=os.path.join(destination_dir,f'{proxy_name}.xml')
    utils.write_file(kvm_policy_path, build_kvm_policy(kvm_data))
    utils.write_file(am_policy_path, build_am_policy(kvm_data))
    utils.write_file(root_proxy_path, build_api_proxy_root(proxy_name,proxy_path))
    utils.create_proxy_bundle(f"{base_dir}/{proxy_name}", proxy_name, f"{base_dir}/{proxy_name}")

# prepare_api_proxy(kvm_data, 'target/apis')