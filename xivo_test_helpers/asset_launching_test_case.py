# -*- coding: utf-8 -*-

# Copyright (C) 2015-2016 Avencall
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

import logging
import os
import subprocess
import unittest

from docker import Client

logger = logging.getLogger(__name__)


class AssetLaunchingTestCase(unittest.TestCase):
    """
    Subclasses of this class MUST have the following fields:

    * service: The name of the service under test in the docker-compose.yml file
    * asset: The name of the asset to run
    * assets_root: The location of the assets
    """

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
        _run_cmd('docker-compose rm --force')
        _run_cmd('docker-compose run --rm sync')

    @classmethod
    def service_status(cls, service_name=None):
        if not service_name:
            service_name = cls.service

        with Client(base_url='unix://var/run/docker.sock') as docker:
            return docker.inspect_container(_container_id(service_name))

    @classmethod
    def service_logs(cls, service_name=None):
        if not service_name:
            service_name = cls.service

        service_id = _run_cmd('docker-compose ps -q {}'.format(service_name)).strip()
        status = _run_cmd('docker logs {container}'.format(container=service_id))
        return status

    @classmethod
    def stop_service_with_asset(cls):
        _run_cmd('docker-compose kill')
        os.chdir(cls.cur_dir)

    @classmethod
    def restart_service(cls, service_name=None):
        if not service_name:
            service_name = cls.service

        with Client(base_url='unix://var/run/docker.sock') as docker:
            docker.restart(_container_id(service_name))

    @classmethod
    def stop_service(cls, service_name=None):
        if not service_name:
            service_name = cls.service

        with Client(base_url='unix://var/run/docker.sock') as docker:
            docker.stop(_container_id(service_name))

    @classmethod
    def _run_cmd(cls, cmd):
        _run_cmd(cmd)


def _run_cmd(cmd, stderr=True):
    with open(os.devnull, "w") as null:
        stderr = subprocess.STDOUT if stderr else null
        process = subprocess.Popen(cmd.split(' '), stdout=subprocess.PIPE, stderr=stderr)
        out, _ = process.communicate()
    logger.info('%s', out)
    return out


def _container_id(service_name):
    result = _run_cmd('docker-compose ps -q {}'.format(service_name), stderr=False).strip()
    result = result.decode('utf-8')
    if '\n' in result:
        raise AssertionError('There is more than one container running with name {}'.format(service_name))
    return result
