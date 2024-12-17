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

from exporter import ApigeeExporter
from classic import ApigeeClassic
from utils import *
from base_logger import logger
import os

seperator = ' | '
DEFAULT_GCP_ENV_TYPE = 'BASE'


def pre_validation_checks(cfg):
    logger.info(
        "------------------- Pre Validation Checks -----------------------")

    # validate input.properties
    required_keys = {
        "inputs": ["SOURCE_URL", "SOURCE_ORG", "SOURCE_AUTH_TYPE", "SOURCE_APIGEE_VERSION","TARGET_DIR"],
        "export": ["EXPORT_DIR", "EXPORT_FILE"],
    }
    missing_keys = []

    for section, keys in required_keys.items():
        if section in cfg:
            section_keys = cfg[section]
            for key in keys:
                if key not in section_keys:
                    missing_keys.append((section, key))
        else:
            logger.error(f"Section {section} is missing in input.properties")
            return False

    if missing_keys:
        logger.error("Missing keys in input.properties:")
        for section, key in missing_keys:
            logger.error(f" - Section: {section}, Key: {key}")
        return False
    else:
        logger.info("All required keys are present in input.properties")

    # check for source org
    SOURCE_URL = cfg.get('inputs', 'SOURCE_URL')
    SOURCE_ORG = cfg.get('inputs', 'SOURCE_ORG')
    SOURCE_AUTH_TOKEN = get_source_auth_token()
    SOURCE_AUTH_TYPE = cfg.get('inputs', 'SOURCE_AUTH_TYPE')
    try:
        SSL_VERIFICATION = cfg.getboolean('inputs', 'SSL_VERIFICATION')
    except ValueError:
        SSL_VERIFICATION = True
    opdk = ApigeeClassic(SOURCE_URL, SOURCE_ORG,
                         SOURCE_AUTH_TOKEN, SOURCE_AUTH_TYPE,SSL_VERIFICATION)
    if (not opdk.get_org()):
        logger.error(f"No source organizations found")
        return False
    return True


def export_artifacts(cfg, resources_list):
    logger.info('------------------- EXPORT -----------------------')
    SOURCE_URL = cfg.get('inputs', 'SOURCE_URL')
    SOURCE_ORG = cfg.get('inputs', 'SOURCE_ORG')
    SOURCE_AUTH_TOKEN = get_source_auth_token()
    SOURCE_AUTH_TYPE = cfg.get('inputs', 'SOURCE_AUTH_TYPE')
    TARGET_DIR = cfg.get('inputs', 'TARGET_DIR')
    try:
        SSL_VERIFICATION = cfg.getboolean('inputs', 'SSL_VERIFICATION')
    except ValueError:
        SSL_VERIFICATION = True
    EXPORT_DIR = f"{TARGET_DIR}/{cfg.get('export','EXPORT_DIR')}"
    apigeeExport = ApigeeExporter(
        SOURCE_URL,
        SOURCE_ORG,
        SOURCE_AUTH_TOKEN,
        SOURCE_AUTH_TYPE,
        SSL_VERIFICATION
    )
    if (os.environ.get("IGNORE_EXPORT") == "true"):
        export_data={}
        export_data["orgConfig"] = apigeeExport.read_export_state(os.path.join(EXPORT_DIR,"orgConfig"))
        export_data["envConfig"] = apigeeExport.read_export_state(os.path.join(EXPORT_DIR,"envConfig"))
    
    else:
        export_data = apigeeExport.get_export_data(resources_list, EXPORT_DIR)
        logger.debug(export_data)
        apigeeExport.create_export_state(EXPORT_DIR)

    return export_data

