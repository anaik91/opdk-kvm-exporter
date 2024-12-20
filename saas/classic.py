#!/usr/bin/python

# Copyright 2023 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License

from rest import RestClient
from requests.utils import quote as urlencode
from base_logger import logger
from time import sleep
import os

class ApigeeClassic():
    def __init__(self, baseurl, org, token, auth_type, ssl_verify):
        self.baseurl = baseurl
        self.org = org
        self.token = token
        self.auth_type = auth_type
        self.client = RestClient(self.auth_type, token, ssl_verify)
        self.requires_pagination = ['apis', 'apps', 'developers', 'apiproducts']
        self.can_expand = {
            'apps': {'expand_key': 'app', 'id': 'appId'},
            'developers': {'expand_key': 'developer', 'id': 'email'},
            'apiproducts': {'expand_key': 'apiProduct', 'id': 'name'}
        }

    def get_org(self):
        url = f"{self.baseurl}/organizations/{self.org}"
        org = self.client.get(url)
        return org

    def list_environments(self):
        url = f"{self.baseurl}/organizations/{self.org}/environments"
        envs = self.client.get(url)
        return envs

    def list_org_objects(self, org_object):
        org_objects = []
        object_count = 100
        if org_object in self.requires_pagination:
            start_url = f"{self.baseurl}/organizations/{self.org}/{org_object}?count={object_count}"
            each_org_object = self.client.get(start_url)
            org_objects.extend(each_org_object)
            while len(each_org_object) > 0:
                startKey = each_org_object[-1]
                params = {'startKey': startKey}
                each_org_object = self.client.get(start_url, params=params)
                each_org_object.remove(startKey)
                org_objects.extend(each_org_object)
        else:
            url = f"{self.baseurl}/organizations/{self.org}/{org_object}"
            org_objects = self.client.get(url)
        return org_objects

    def list_org_objects_expand(self, org_object):
        org_objects = {}
        object_count = 100
        expand_key = self.can_expand.get(org_object).get('expand_key')
        id_key = self.can_expand.get(org_object).get('id')
        start_url = f"{self.baseurl}/organizations/{self.org}/{org_object}?count={object_count}&expand=true"
        each_org_object = self.client.get(start_url)
        each_org_object = each_org_object.get(expand_key,{})
        for each_item in each_org_object:
            org_objects[each_item[id_key]] = each_item
        while len(each_org_object) > 0:
            startKey = each_org_object[-1].get(id_key)
            params = {'startKey': startKey}
            each_org_object = self.client.get(start_url, params=params)
            each_org_object = each_org_object.get(expand_key,{})
            each_org_object.pop(0)
            for each_item in each_org_object:
                org_objects[each_item[id_key]] = each_item
        return org_objects

    def get_org_object(self, org_object, org_object_name):
        if org_object == "resourcefiles":
            type = org_object_name["type"]
            name = org_object_name["name"]
            url = f"{self.baseurl}/organizations/{self.org}/{org_object}/{type}/{name}"
            data = self.client.get(url)
            return data
        else:
            org_object_name = urlencode(org_object_name)
            url = f"{self.baseurl}/organizations/{self.org}/{org_object}/{org_object_name}"
            org_object = self.client.get(url)
            return org_object

    def list_env_objects(self, env, env_object):
        url = f"{self.baseurl}/organizations/{self.org}/environments/{env}/{env_object}"
        env_objects = self.client.get(url)
        return env_objects

    def get_env_object(self, env, env_object, env_object_name):
        if env_object == "resourcefiles":
            type = env_object_name["type"]
            name = env_object_name["name"]
            url = f"{self.baseurl}/organizations/{self.org}/environments/{env}/{env_object}/{type}/{name}"
            data = self.client.get(url)
        else:
            env_object_name = urlencode(env_object_name)
            url = f"{self.baseurl}/organizations/{self.org}/environments/{env}/{env_object}/{env_object_name}"
            data = self.client.get(url)
        return data

    def list_env_vhosts(self, env):
        url = f"{self.baseurl}/organizations/{self.org}/environments/{env}/virtualhosts"
        env_objects = self.client.get(url)
        return env_objects

    def get_env_vhost(self, env, vhost):
        url = f"{self.baseurl}/organizations/{self.org}/environments/{env}/virtualhosts/{vhost}"
        env_object = self.client.get(url)
        return env_object

    def list_apis(self, api_type):
        url = f"{self.baseurl}/organizations/{self.org}/{api_type}"
        apis = self.client.get(url)
        return apis

    def list_api_revisions(self, api_type, api_name):
        url = f"{self.baseurl}/organizations/{self.org}/{api_type}/{api_name}/revisions"
        revisions = self.client.get(url)
        return revisions

    def api_env_mapping(self, api_type, api_name):
        url = f"{self.baseurl}/organizations/{self.org}/{api_type}/{api_name}/deployments"
        deployments = self.client.get(url)
        return deployments

    def list_apis_env(self, env_name):
        url = f"{self.baseurl}/organizations/{self.org}/environments/{env_name}/deployments"
        deployments = self.client.get(url)
        apis_list = [api["name"] for api in deployments["aPIProxy"]]
        return apis_list

    def fetch_api_revision(self, api_type, api_name, revision, export_dir):
        url = f"{self.baseurl}/organizations/{self.org}/{api_type}/{api_name}/revisions/{revision}?format=bundle"
        bundle = self.client.file_get(url)
        self.write_proxy_bundle(export_dir, api_name, bundle)

    def write_proxy_bundle(self, export_dir, file_name, data):
        file_path = f"./{export_dir}/{file_name}.zip"
        with open(file_path, 'wb') as fl:
            fl.write(data)

    def fetch_proxy(self, arg_tuple):
        revisions = self.list_api_revisions(arg_tuple[0], arg_tuple[1])
        self.fetch_api_revision(
            arg_tuple[0], arg_tuple[1], revisions[-1], arg_tuple[2])

    def view_pod_component_details(self, pod):
        url = f"{self.baseurl}/servers?pod={pod}"
        view_pod_response = self.client.get(url)
        return view_pod_response
    
    def get_api(self, api_type, api_name):
        url = f"{self.baseurl}/organizations/{self.org}/{api_type}/{api_name}"
        data = self.client.get(url)
        return data
    
    def create_api(self, api_name, proxy_bundle_path):
        url = f"{self.baseurl}/organizations/{self.org}/apis?action=import&name={api_name}&validate=true"
        logger.info(url)
        proxy_bundle_name = os.path.basename(proxy_bundle_path)
        # params = {
        #     'name': api_name,
        #     'action': 'import',
        #     # 'validate': True
        # }
        files = [
            ('file', (proxy_bundle_name, open(proxy_bundle_path, 'rb'), 'application/zip'))
        ]

        api_object = self.client.file_post(url, {}, {}, files)
        return api_object
    
    def deploy_api(self, env_name, api_type, api_name, revision):
        url= f"{self.baseurl}/organizations/{self.org}/environments/{env_name}/{api_type}/{api_name}/revisions/{revision}/deployments?override=true"
        data = self.client.post(url)
        return data
    
    def get_api_revisions_deployment(self,env_name,api_type, api_name, revision):
        url = f"{self.baseurl}/organizations/{self.org}/environments/{env_name}/{api_type}/{api_name}/revisions/{revision}/deployments"
        data = self.client.get(url)
        return data

    def deploy_api_bundle(self, env_name, api_type, api_name, proxy_bundle_path, api_force_redeploy=False):  # noqa
        api_deployment_retry = 60
        api_deployment_sleep = 5
        api_deployment_retry_count = 0
        api_exists = False
        get_api_status = self.get_api(api_type, api_name)
        if get_api_status.get('metaData'):
            api_exists = True
            api_rev = get_api_status.get('revision', ['1'])[-1]
            logger.warning(f"Proxy with name {api_name} with revision {api_rev} already exists in Apigee Org {self.org}")  # noqa
            if api_force_redeploy:
                api_exists = False
        if not api_exists:
            api_created = self.create_api(api_name, proxy_bundle_path)
            if api_created.get('name'):
                logger.info(f"Proxy has been imported with name {api_name} in Apigee Org {self.org}")  # noqa
                api_exists = True
                api_rev = api_created.get('revision')
            else:
                logger.error(f"ERROR : Proxy {api_name} import failed !!! ")
                return False
        if api_exists:
            if not self.get_api_revisions_deployment(
                        env_name, api_type, api_name, api_rev
                    ).get('code','') == 'distribution.RevisionNotDeployed':
                logger.info(f"Proxy {api_name} already active in to {env_name} in Apigee Org {self.org} !")  # noqa
                return True
            else:
                if self.deploy_api(env_name, api_type, api_name, api_rev):
                    logger.info(f"Deploying proxy with name {api_name}  to {env_name} in Apigee Org {self.org}")  # noqa
                    while api_deployment_retry_count < api_deployment_retry:
                        if not self.get_api_revisions_deployment(
                            env_name, api_type, api_name, api_rev
                        ).get('code','') == 'distribution.RevisionNotDeployed':
                            logger.info(f"Proxy {api_name} active in runtime after {api_deployment_retry_count*api_deployment_sleep} seconds ")  # noqa
                            return True
                        else:
                            logger.debug(f"Checking API deployment status in {api_deployment_sleep} seconds")  # noqa
                            sleep(api_deployment_sleep)
                            api_deployment_retry_count += 1
                else:
                    logger.error(f"ERROR : Proxy deployment  to {env_name} in Apigee Org {self.org} Failed !!")  # noqa
                    return False
