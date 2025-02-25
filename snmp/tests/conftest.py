# (C) Datadog, Inc. 2018
# All rights reserved
# Licensed under Simplified BSD License (see LICENSE)

import os
import shutil

import pytest
import requests

from datadog_checks.dev import TempDir, docker_run

from .common import COMPOSE_DIR, SCALAR_OBJECTS, SCALAR_OBJECTS_WITH_TAGS, TABULAR_OBJECTS, generate_instance_config

FILES = ["https://ddintegrations.blob.core.windows.net/snmp/f5.snmprec"]


@pytest.fixture(scope='session')
def dd_environment():
    with TempDir('snmprec', COMPOSE_DIR) as tmp_dir:
        data_dir = os.path.join(tmp_dir, 'data')
        env = {'DATA_DIR': data_dir}
        if not os.path.exists(data_dir):
            shutil.copytree(os.path.join(COMPOSE_DIR, 'data'), data_dir)
            for data_file in FILES:
                response = requests.get(data_file)
                with open(os.path.join(data_dir, data_file.rsplit('/', 1)[1]), 'wb') as output:
                    output.write(response.content)

        with docker_run(os.path.join(COMPOSE_DIR, 'docker-compose.yaml'), env_vars=env, log_patterns="Listening at"):
            yield generate_instance_config(SCALAR_OBJECTS + SCALAR_OBJECTS_WITH_TAGS + TABULAR_OBJECTS)
