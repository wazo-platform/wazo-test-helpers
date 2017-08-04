# -*- coding: utf-8 -*-
# Copyright 2015-2017 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0+

import logging
import os
import subprocess
import unittest

import docker as docker_client

logger = logging.getLogger(__name__)

if os.environ.get('TEST_LOGS') != 'verbose':
    logging.getLogger('requests.packages.urllib3.connectionpool').setLevel(logging.WARNING)
    logging.getLogger('docker.auth').setLevel(logging.INFO)
    logger.setLevel(logging.WARNING)


class NoSuchService(Exception):
    def __init__(self, service_name):
        super(NoSuchService, self).__init__('No such service: {}'.format(service_name))


class NoSuchPort(Exception):
    def __init__(self, service_name, port):
        super(NoSuchPort, self).__init__('For service {}: No such port: {}'.format(service_name, port))


class AssetLaunchingTestCase(unittest.TestCase):
    """
    Subclasses of this class MUST have the following fields:

    * service: The name of the service under test in the docker-compose.yml file
    * asset: The name of the asset to run
    * assets_root: The location of the assets
    """

    cur_dir = None

    @classmethod
    def setUpClass(cls):
        cls.container_name = cls.asset
        asset_path = os.path.join(cls.assets_root, cls.asset)
        cls.pushd(asset_path)
        cls.launch_service_with_asset()

    @classmethod
    def tearDownClass(cls):
        cls.stop_service_with_asset()
        cls.popd()

    @classmethod
    def launch_service_with_asset(cls):
        logger.debug('Removing containers...')
        cls.rm_containers()
        logger.debug('Done.')
        logger.debug('Starting containers...')
        cls.start_containers(bootstrap_container='sync')
        logger.debug('Done.')

    @classmethod
    def pushd(cls, path):
        cls.cur_dir = os.getcwd()
        os.chdir(path)

    @classmethod
    def popd(cls):
        if cls.cur_dir:
            os.chdir(cls.cur_dir)

    @classmethod
    def rm_containers(cls):
        _run_cmd(['docker-compose', 'rm', '--force'])

    @classmethod
    def start_containers(cls, bootstrap_container):
        _run_cmd(['docker-compose', 'run', '--rm', bootstrap_container])

    @classmethod
    def kill_containers(cls):
        _run_cmd(['docker-compose', 'kill'])

    @classmethod
    def log_containers(cls):
        return _run_cmd(['docker-compose', 'logs', '--no-color'])

    @classmethod
    def service_status(cls, service_name=None):
        if not service_name:
            service_name = cls.service

        docker = docker_client.from_env().api
        return docker.inspect_container(_container_id(service_name))

    @classmethod
    def service_logs(cls, service_name=None):
        if not service_name:
            service_name = cls.service

        status = _run_cmd(['docker', 'logs', _container_id(service_name)])
        return status

    @classmethod
    def service_port(cls, internal_port, service_name=None):
        if not service_name:
            service_name = cls.service

        docker = docker_client.from_env().api
        result = docker.port(_container_id(service_name), internal_port)

        if not result:
            raise NoSuchPort(service_name, internal_port)

        return int(result[0]['HostPort'])

    @classmethod
    def stop_service_with_asset(cls):
        logger.debug('Killing containers...')
        cls.kill_containers()
        logger.debug('Done.')

    @classmethod
    def restart_service(cls, service_name=None):
        if not service_name:
            service_name = cls.service

        docker = docker_client.from_env().api
        docker.restart(_container_id(service_name))

    @classmethod
    def stop_service(cls, service_name=None):
        if not service_name:
            service_name = cls.service

        docker = docker_client.from_env().api
        docker.stop(_container_id(service_name))

    @classmethod
    def start_service(cls, service_name=None):
        if not service_name:
            service_name = cls.service

        docker = docker_client.from_env().api
        docker.start(_container_id(service_name))

    def docker_exec(cls, command, service_name=None):
        if not service_name:
            service_name = cls.service

        docker_command = ['docker', 'exec', _container_id(service_name)] + command
        return _run_cmd(docker_command)

    @classmethod
    def _run_cmd(cls, cmd):
        _run_cmd(cmd.split(' '))


def _run_cmd(cmd, stderr=True):
    with open(os.devnull, "w") as null:
        stderr = subprocess.STDOUT if stderr else null
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=stderr)
        out, _ = process.communicate()
    logger.info('%s', out)
    return out


def _container_id(service_name):
    result = _run_cmd(['docker-compose', 'ps', '-q', service_name], stderr=False).strip()
    result = result.decode('utf-8')
    if '\n' in result:
        raise AssertionError('There is more than one container running with name {}'.format(service_name))
    if not result:
        raise NoSuchService(service_name)
    return result
