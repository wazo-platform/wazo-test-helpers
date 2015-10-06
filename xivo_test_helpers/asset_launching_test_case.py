# -*- coding: utf-8 -*-

# Copyright (C) 2015 Avencall
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>

import json
import logging
import os
import subprocess
import unittest

logger = logging.getLogger(__name__)


class AssetLaunchingTestCase(unittest.TestCase):
    """
    Subclasses of this class should have a service field containing the name of
    the service under test and an asset field containing the name of the asset
    folder to execute.
    """

    assets_root = os.path.join(os.path.dirname(__file__), '..', 'assets')

    @classmethod
    def setUpClass(cls):
        cls.launch_service_with_asset()

    @classmethod
    def tearDownClass(cls):
        cls.stop_service_with_asset()

    @classmethod
    def launch_service_with_asset(cls):
        cls.container_name = cls.asset
        asset_path = os.path.join(cls.assets_root, cls.asset)
        cls.cur_dir = os.getcwd()
        os.chdir(asset_path)
        cls._run_cmd('docker-compose rm --force')
        cls._run_cmd('docker-compose run --rm sync')

    @classmethod
    def service_status(cls):
        service_id = cls._run_cmd('docker-compose ps -q {}'.format(cls.service)).strip()
        status = cls._run_cmd('docker inspect {container}'.format(container=service_id))
        return json.loads(status)

    @classmethod
    def service_logs(cls):
        service_id = cls._run_cmd('docker-compose ps -q {}'.format(cls.service)).strip()
        status = cls._run_cmd('docker logs {container}'.format(container=service_id))
        return status

    @staticmethod
    def _run_cmd(cmd):
        process = subprocess.Popen(cmd.split(' '), stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        out, _ = process.communicate()
        logger.info(out)
        return out

    @classmethod
    def stop_service_with_asset(cls):
        cls._run_cmd('docker-compose kill')
        os.chdir(cls.cur_dir)
