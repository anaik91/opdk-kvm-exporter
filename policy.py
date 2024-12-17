import json

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
    <KeyValueMapOperations name="getEncrypted" mapIdentifier="{kvm_data.get('name')}">
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

kvm_data={}
print(build_kvm_policy(kvm_data))

print(build_am_policy(kvm_data))