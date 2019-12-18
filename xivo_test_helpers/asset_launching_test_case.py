# -*- coding: utf-8 -*-
# Copyright 2015-2019 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

import logging
import os
import random
import string
import subprocess
import tempfile
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
    def __init__(self, stdout, stderr, return_code):
        message = 'Container start failed (code {}): output follows.\nstdout:\n{}\nstderr:\n{}'.format(return_code, stdout, stderr)
        super(ContainerStartFailed, self).__init__(message)

        self.stdout = stdout
        self.stderr = stderr
        self.return_code = return_code


class AssetLaunchingTestCase(unittest.TestCase):
    """
    Subclasses of this class MUST have the following fields:

    * service: The name of the service under test in the docker-compose.yml file
    * asset: The name of the asset to run
    * assets_root: The location of the assets
    """

    cur_dir = None
    log_dir = None

    @staticmethod
    def get_log_directory():
        if not AssetLaunchingTestCase.log_dir:
            char_set = string.ascii_lowercase
            default_logging_dir = '/tmp/wazo-integration-{}'.format(
                ''.join(random.choice(char_set) for _ in range(8))
            )
            AssetLaunchingTestCase.log_dir = os.getenv('WAZO_TEST_DOCKER_LOGS_DIR', default_logging_dir)
            if not os.path.exists(AssetLaunchingTestCase.log_dir):
                os.makedirs(AssetLaunchingTestCase.log_dir, mode=0o755)
        return AssetLaunchingTestCase.log_dir

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
                 ['down', '--timeout', '0', '--volumes'])

    @classmethod
    def start_containers(cls, bootstrap_container):
        completed_process = _run_cmd(['docker-compose'] + cls._docker_compose_options() +
                                     ['run', '--rm', bootstrap_container])
        if completed_process.returncode != 0:
            raise ContainerStartFailed(stdout=completed_process.stdout.decode('unicode-escape'),
                                       stderr=completed_process.stderr.decode('unicode-escape'),
                                       return_code=completed_process.returncode)

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
    def service_logs(cls, service_name=None, since=None):
        if not service_name:
            service_name = cls.service

        cmd = ['docker', 'logs', cls._container_id(service_name)]
        if since is not None:
            cmd.append(f'--since={since}')
        status = _run_cmd(cmd).stdout
        return status.decode('utf-8')

    @classmethod
    def database_logs(cls, service_name='postgres', since=None):
        logs = cls.service_logs(service_name=service_name, since=since)
        return logs.replace('\n\t', ' ')

    @classmethod
    def count_database_logs(cls, service_name='postgres', since=None):
        logs = cls.database_logs(service_name=service_name, since=since)
        return len(logs.split('\n'))

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
        if os.getenv('WAZO_TEST_DOCKER_LOGS_ENABLED', '0') == '1':
            filename_prefix = '{}.{}-'.format(cls.__module__, cls.__name__)
            with tempfile.NamedTemporaryFile(dir=cls.get_log_directory(),
                                             prefix=filename_prefix,
                                             delete=False) as logfile:
                logfile.write(cls.log_containers())
                logger.debug('Container logs dumped to %s', logfile.name)
        logger.debug('Done.')

    @classmethod
    def restart_service(cls, service_name=None, signal=None):
        if not service_name:
            service_name = cls.service

        docker = docker_client.from_env().api
        container_id = cls._container_id(service_name)
        if signal:
            docker.kill(container_id, signal=signal)
        docker.restart(container_id)

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
        options = [
            '--no-ansi',
            '--project-name', cls.service,
            '--file', os.path.join(cls.assets_root, 'docker-compose.yml'),
            '--file', os.path.join(
                cls.assets_root, 'docker-compose.{}.override.yml'.format(cls.asset)
            ),
        ]
        extra = os.getenv("WAZO_TEST_DOCKER_OVERRIDE_EXTRA")
        if extra:
            options.extend(["--file", extra])
        return options


class CompletedProcess(object):
    '''Partially bakported from python3 subprocess'''

    def __init__(self, process):
        self.stdout, self.stderr = process.communicate()
        self.stdout = self.stdout or b''
        self.stderr = self.stderr or b''
        self.returncode = process.returncode


def _run_cmd(cmd, stderr=True):
    logger.debug('%s', cmd)
    with open(os.devnull, "w") as null:
        stderr = subprocess.STDOUT if stderr else null
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=stderr)
        completed_process = CompletedProcess(process)
    logger.info('%s', completed_process.stdout)
    return completed_process
