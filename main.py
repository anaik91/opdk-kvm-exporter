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

from core_wrappers import *
from utils import (
    write_json,
    parse_json,
)
from base_logger import logger

def main():
    # Parse Input
    cfg = parse_config('input.properties')
    resources_list = ['org_keyvaluemaps', 'keyvaluemaps']
    # Pre validation checks
    if(not pre_validation_checks(cfg)):
        logger.error("Pre validation checks failed. Please, check...")
        return

    export_data_file = f"{cfg.get('inputs', 'TARGET_DIR')}/{cfg.get('export','EXPORT_DIR')}/{cfg.get('export', 'EXPORT_FILE')}"
    export_data = parse_json(export_data_file)

    if not export_data.get('export', False):
        export_data['export'] = False
        export_data = export_artifacts(cfg, resources_list)
        export_data['export'] = True
        write_json(export_data_file, export_data)


if __name__ == '__main__':
    main()