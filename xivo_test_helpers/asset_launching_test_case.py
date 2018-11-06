# -*- coding: utf-8 -*-
# Copyright 2015-2018 The Wazo Authors  (see the AUTHORS file)
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


class ContainerStartFailed(Exception):
    def __init__(self, output):
        super(ContainerStartFailed, self).__init__('Container start failed: {}'.format(output))
        self.output = output


class AssetLaunchingTestCase(unittest.TestCase):
    """
    Subclasses of this class MUST have the following fields:

    * service: The name of the service under test in the docker-compose.yml file
    * asset: The name of the asset to run
    * assets_root: The location of the assets
    """

    cur_dir = None

    @staticmethod
    def is_managing_containers():
        return os.environ.get('TEST_DOCKER', 'manage') != 'ignore'

    @classmethod
    def setUpClass(cls):
        if cls.is_managing_containers():
            cls.launch_service_with_asset()
        else:
            logger.debug('Container management disabled.')

    @classmethod
    def tearDownClass(cls):
        if cls.is_managing_containers():
            cls.stop_service_with_asset()
        else:
            logger.debug('Container management disabled.')

    @classmethod
    def launch_service_with_asset(cls):
        logger.debug('Removing containers...')
        cls.rm_containers()
        logger.debug('Done.')
        logger.debug('Starting containers...')
        try:
            cls.start_containers(bootstrap_container='sync')
        except ContainerStartFailed as e:
            logger.error(e)
            cls.kill_containers()
            raise
        logger.debug('Done.')

    @classmethod
    def rm_containers(cls):
        _run_cmd(['docker-compose'] + cls._docker_compose_options() +
                 ['down', '--timeout', '0'])

    @classmethod
    def start_containers(cls, bootstrap_container):
        completed_process = _run_cmd(['docker-compose'] + cls._docker_compose_options() +
                                     ['run', '--rm', bootstrap_container])
        if completed_process.returncode != 0:
            raise ContainerStartFailed(output=completed_process.stdout.decode('unicode-escape'))

    @classmethod
    def kill_containers(cls):
        _run_cmd(['docker-compose'] + cls._docker_compose_options() +
                 ['kill'])

    @classmethod
    def log_containers(cls):
        return _run_cmd(['docker-compose'] + cls._docker_compose_options() +
                        ['logs', '--no-color']).stdout

    @classmethod
    def service_status(cls, service_name=None):
        if not service_name:
            service_name = cls.service

        docker = docker_client.from_env().api
        return docker.inspect_container(cls._container_id(service_name))

    @classmethod
    def service_logs(cls, service_name=None):
        if not service_name:
            service_name = cls.service

        status = _run_cmd(['docker', 'logs', cls._container_id(service_name)]).stdout
        return status.decode('utf-8')

    @classmethod
    def service_port(cls, internal_port, service_name=None):
        if not service_name:
            service_name = cls.service

        docker = docker_client.from_env().api
        result = docker.port(cls._container_id(service_name), internal_port)

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
        docker.restart(cls._container_id(service_name))

    @classmethod
    def stop_service(cls, service_name=None, timeout=10):
        if not service_name:
            service_name = cls.service

        docker = docker_client.from_env(timeout=timeout).api
        docker.stop(cls._container_id(service_name))

    @classmethod
    def start_service(cls, service_name=None):
        if not service_name:
            service_name = cls.service

        docker = docker_client.from_env().api
        docker.start(cls._container_id(service_name))

    @classmethod
    def docker_exec(cls, command, service_name=None):
        if not service_name:
            service_name = cls.service

        docker_command = ['docker', 'exec', cls._container_id(service_name)] + command
        return _run_cmd(docker_command).stdout

    @classmethod
    def _run_cmd(cls, cmd):
        _run_cmd(cmd.split(' '))

    @classmethod
    def _container_id(cls, service_name):
        result = _run_cmd(['docker-compose'] + cls._docker_compose_options() +
                          ['ps', '-q', service_name], stderr=False).stdout.strip()
        result = result.decode('utf-8')
        if '\n' in result:
            raise AssertionError('There is more than one container running with name {}'.format(service_name))
        if not result:
            raise NoSuchService(service_name)
        return result

    @classmethod
    def _docker_compose_options(cls):
        return [
            '--file', os.path.join(cls.assets_root, cls.asset, 'docker-compose.yml'),
            # separator is 0, because docker-compose does not allow anything other than [a-z0-9]...
            '--project-name', '{project}0{asset}'.format(project=cls.service, asset=cls.asset),
        ]


class CompletedProcess(object):
    '''Partially bakported from python3 subprocess'''

    def __init__(self, process):
        self.stdout, self.stderr = process.communicate()
        self.returncode = process.returncode


def _run_cmd(cmd, stderr=True):
    logger.debug('%s', cmd)
    with open(os.devnull, "w") as null:
        stderr = subprocess.STDOUT if stderr else null
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=stderr)
        completed_process = CompletedProcess(process)
    logger.info('%s', completed_process.stdout)
    return completed_process
