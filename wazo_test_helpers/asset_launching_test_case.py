# Copyright 2015-2026 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

import logging
import os
import random
import string
import subprocess
import tempfile
import unittest
from asyncio import Future
from collections.abc import Callable, Generator, Iterator
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any, Generic, NoReturn, TextIO, TypeVar, cast

import docker as docker_client

if TYPE_CHECKING:
    from tempfile import _TemporaryFileWrapper
    from typing import ParamSpec

    P = ParamSpec('P')


ClassType = TypeVar("ClassType", bound=type[Any])
R = TypeVar('R')

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

if os.environ.get('TEST_LOGS') != 'verbose':
    logging.getLogger('amqp').setLevel(logging.INFO)
    logging.getLogger('docker').setLevel(logging.INFO)
    logging.getLogger('stevedore.extension').setLevel(logging.INFO)
    logging.getLogger('urllib3.connectionpool').setLevel(logging.WARNING)
    logger.setLevel(logging.WARNING)


class ClientCreateException(Exception):
    def __init__(self, client_name: str) -> None:
        super().__init__(f'Could not create client {client_name}')


class WrongClient:
    def __init__(self, client_name: str) -> None:
        self.client_name = client_name

    def __getattr__(self, member: str) -> NoReturn:
        raise ClientCreateException(self.client_name)


class NoSuchService(Exception):
    def __init__(self, service_name: str) -> None:
        super().__init__(f'No such service: {service_name}')


class NoSuchPort(Exception):
    def __init__(self, service_name: str, port: int | str) -> None:
        super().__init__(f'For service {service_name}: No such port: {port}')


class ContainerStartFailed(Exception):
    def __init__(self, stdout: str, stderr: str, return_code: int) -> None:
        message = (
            f'Container start failed (code {return_code}): '
            f'output follows.\nstdout:\n{stdout}\nstderr:\n{stderr}'
        )
        super().__init__(message)

        self.stdout = stdout
        self.stderr = stderr
        self.return_code = return_code


class ContainerCommandFailed(Exception):
    def __init__(
        self, command: list[str], service_name: str, return_code: int | str | list[str]
    ):
        command_str = ' '.join(command)
        message = (
            f'An error occured while trying to run command: `{command_str}` '
            f'(service: {service_name}, return_code: {return_code})'
        )
        super().__init__(message)


class CachedClassProperty(Generic[R]):
    __slots__ = ('_func', '_value')

    def __init__(self, func: Callable[[ClassType], R]) -> None:
        self._func = func

    def __get__(self, instance: object | None, owner: ClassType | None = None) -> R:
        if owner is None:
            owner = cast(ClassType, type(instance))
        if not hasattr(self, '_value'):
            self._value = self._func(owner)
            return self._value
        return cast(R, getattr(self, '_value'))

    def __del__(self, obj: object | None = None) -> None:
        if hasattr(self, '_value'):
            delattr(self, '_value')


cached_class_property = CachedClassProperty


def get_container_management_enabled() -> bool:
    return os.environ.get('TEST_DOCKER', 'manage') != 'ignore'


def require_container_management(func: Callable[P, R]) -> Callable[P, R | None]:
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R | None:
        if get_container_management_enabled():
            return func(*args, **kwargs)
        logger.debug('Container management disabled.')
        return None

    return wrapper


class AbstractAssetLaunchingHelper:
    """
    The following three attributes must be defined on subclasses.
    """

    service: str  # The name of the service under test in the docker-compose.yml file
    asset: str  # The name of the asset to run, e.g 'base'
    assets_root: str | Path  # Root path for storing assets

    cur_dir: str | Path | None = None
    log_dir: str | Path | None = None

    @classmethod
    @require_container_management
    def launch_service_with_asset(cls) -> None:
        logger.debug('Removing containers...')
        cls.rm_containers()
        logger.debug('Done.')

        if os.getenv('WAZO_TEST_NO_DOCKER_COMPOSE_PULL') == '1':
            logger.debug('Not Pulling containers.')
        else:
            logger.debug('Pulling containers...')
            cls.pull_containers()
            logger.debug('Done.')

        logger.debug('Starting containers...')
        try:
            cls.start_containers(bootstrap_container='sync')
        except ContainerStartFailed as e:
            logger.error(e)

            cls.stop_services()
            cls._maybe_dump_docker_logs()
            cls._maybe_collect_coverage()
            raise
        logger.debug('Done.')

    @classmethod
    def rm_containers(cls) -> None:
        _run_cmd(
            ['docker', 'compose']
            + cls._docker_compose_options()
            + ['down', '--timeout', '0', '--volumes']
        )

    @classmethod
    def pull_containers(cls) -> None:
        _run_cmd(
            ['docker', 'compose']
            + cls._docker_compose_options()
            + ['pull', '--ignore-pull-failures']
        )

    @classmethod
    @require_container_management
    def run_container(cls, service_name: str, stderr: bool = True) -> str:
        completed_process = _run_cmd(
            ['docker', 'compose']
            + cls._docker_compose_options()
            + ['run', '--rm', service_name],
            stderr=stderr,
        )
        if completed_process.returncode != 0:
            stdout = completed_process.stdout
            stderr = completed_process.stderr
            raise ContainerStartFailed(
                stdout=stdout.decode('unicode-escape') if stdout else None,
                stderr=stderr.decode('unicode-escape') if stderr else None,
                return_code=completed_process.returncode,
            )

        return completed_process.stdout.decode('utf-8')

    @classmethod
    @require_container_management
    def start_containers(cls, bootstrap_container: str) -> None:
        completed_process = _run_cmd(
            ['docker', 'compose']
            + cls._docker_compose_options()
            + ['run', '--rm', bootstrap_container]
        )
        if completed_process.returncode != 0:
            stdout = completed_process.stdout
            stderr = completed_process.stderr
            raise ContainerStartFailed(
                stdout=stdout.decode('unicode-escape') if stdout else None,
                stderr=stderr.decode('unicode-escape') if stderr else None,
                return_code=completed_process.returncode,
            )

    @classmethod
    @require_container_management
    def stop_services(cls) -> None:
        if cls._is_coverage_enabled():
            cls.stop_containers()
        else:
            cls.kill_containers()

    @classmethod
    @require_container_management
    def kill_containers(cls) -> None:
        logger.debug('Killing containers...')
        _run_cmd(['docker', 'compose'] + cls._docker_compose_options() + ['kill'])

    @classmethod
    @require_container_management
    def stop_containers(cls) -> None:
        logger.debug('Stopping containers...')
        _run_cmd(['docker', 'compose'] + cls._docker_compose_options() + ['stop'])

    @classmethod
    def log_containers(cls) -> str:
        return _run_cmd(
            ['docker', 'compose']
            + cls._docker_compose_options()
            + ['logs', '--no-color']
        ).stdout

    @classmethod
    def log_containers_to_file(
        cls, log_file: TextIO | _TemporaryFileWrapper
    ) -> subprocess.CompletedProcess:
        return subprocess.run(
            ['docker', 'compose']
            + cls._docker_compose_options()
            + ['logs', '--no-color'],
            stdout=log_file,
        )

    @classmethod
    def service_status(cls, service_name: str | None = None) -> dict:
        if not service_name:
            service_name = cls.service
        docker = docker_client.from_env().api
        return docker.inspect_container(cls._container_id(service_name))

    @classmethod
    def service_logs(
        cls, service_name: str | None = None, since: str | None = None
    ) -> str:
        if not service_name:
            service_name = cls.service

        cmd = ['docker', 'logs', cls._container_id(service_name)]
        if since is not None:
            cmd.append(f'--since={since}')
        status = _run_cmd(cmd).stdout
        return status.decode('utf-8')

    @classmethod
    @contextmanager
    def capture_logs(cls, service_name: str | None = None) -> Iterator[Future]:
        '''
        Usage:
        with self.capture_logs(service_name='auth') as logs:
            client.token.new(expiration=1)
        assert 'login' in logs.result()
        '''
        time_start = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%fZ')
        result: Future = Future()
        try:
            yield result
        finally:
            result.set_result(cls.service_logs(service_name, since=time_start))

    @classmethod
    def database_logs(
        cls, service_name: str = 'postgres', since: str | None = None
    ) -> str:
        logs = cls.service_logs(service_name=service_name, since=since)
        return logs.replace('\n\t', ' ')

    @classmethod
    def count_database_logs(
        cls,
        service_name: str = 'postgres',
        since: str | None = None,
        exclude: str | None = None,
    ) -> int:
        logs = cls.database_logs(service_name=service_name, since=since)
        return len(
            list(
                line for line in logs.split('\n') if not exclude or exclude not in line
            )
        )

    @classmethod
    def database_grant_superuser(
        cls, user: str, service_name: str = 'postgres'
    ) -> None:
        command = ['psql', '-c', f'ALTER ROLE "{user}" WITH SUPERUSER;']
        return_code = cls.docker_exec(
            command, return_attr='returncode', service_name=service_name
        )
        if return_code:
            raise ContainerCommandFailed(command, service_name, return_code)

    @classmethod
    def service_port(cls, internal_port: int, service_name: str | None = None) -> int:
        if not service_name:
            service_name = cls.service

        docker = docker_client.from_env().api
        result = docker.port(cls._container_id(service_name), internal_port)

        if not result:
            raise NoSuchPort(service_name, internal_port)

        # NOTE: This returns the port bound to IPv4 address. You must combine
        # this port with host 127.0.0.1, not localhost, because localhost can
        # resolve to an IPv6 address that would not match with this port.
        return int(result[0]['HostPort'])

    @classmethod
    @require_container_management
    def stop_service_with_asset(cls) -> None:
        cls.stop_services()
        cls._maybe_dump_docker_logs()
        cls._maybe_collect_coverage()
        logger.debug('Done.')

    @classmethod
    def restart_service(
        cls, service_name: str | None = None, signal: str | int | None = None
    ) -> None:
        docker = docker_client.from_env().api
        container_id = cls._container_id(service_name or cls.service)
        if signal:
            docker.kill(container_id, signal=signal)
        docker.restart(container_id)

    @classmethod
    def stop_service(cls, service_name: str | None = None, timeout: int = 10) -> None:
        docker = docker_client.from_env(timeout=timeout).api
        docker.stop(cls._container_id(service_name or cls.service))

    @classmethod
    def start_service(cls, service_name: str | None = None) -> None:
        docker = docker_client.from_env().api
        docker.start(cls._container_id(service_name or cls.service))

    @classmethod
    def pause_service(cls, service_name: str | None = None) -> None:
        docker = docker_client.from_env().api
        docker.pause(cls._container_id(service_name or cls.service))

    @classmethod
    def unpause_service(cls, service_name: str | None = None) -> None:
        docker = docker_client.from_env().api
        docker.unpause(cls._container_id(service_name or cls.service))

    @classmethod
    def docker_exec(
        cls,
        command: list[str],
        service_name: str | None = None,
        return_attr: str = 'stdout',
        privileged: bool = False,
    ) -> str | int | list[str]:
        if not service_name:
            service_name = cls.service

        docker_command = ['docker', 'exec']
        if privileged:
            docker_command.append('--privileged')

        docker_command += [cls._container_id(service_name or cls.service)] + command
        result = _run_cmd(docker_command)
        return getattr(result, return_attr)

    @classmethod
    def docker_copy_to_container(
        cls, src: str, dst: str, service_name: str | None = None
    ) -> subprocess.CompletedProcess:
        container_dst = f'{cls._container_id(service_name or cls.service)}:{dst}'
        docker_command = ['docker', 'cp', src, container_dst]
        return _run_cmd(docker_command)

    @classmethod
    def docker_copy_from_container(
        cls, src: str, dst: str, service_name: str | None = None
    ) -> subprocess.CompletedProcess:
        container_src = f'{cls._container_id(service_name or cls.service)}:{src}'
        docker_command = ['docker', 'cp', container_src, dst]
        return _run_cmd(docker_command)

    @classmethod
    def docker_copy_across_containers(
        cls, src_service_name: str, src: str, dst_service_name: str, dst: str
    ) -> None:
        container_src = f'{cls._container_id(src_service_name)}:{src}'
        container_dst = f'{cls._container_id(dst_service_name)}:{dst}'
        with tempfile.TemporaryDirectory() as tmp_dirname:
            tmp_filename = os.path.join(tmp_dirname, 'docker_cp_across_containers')
            docker_command = ['docker', 'cp', container_src, tmp_filename]
            _run_cmd(docker_command)
            docker_command = ['docker', 'cp', tmp_filename, container_dst]
            _run_cmd(docker_command)

    @classmethod
    def _run_cmd(cls, cmd: str) -> None:
        _run_cmd(cmd.split(' '))

    @classmethod
    def _container_id(cls, service_name: str) -> str:
        result = _run_cmd(
            ['docker', 'compose']
            + cls._docker_compose_options()
            + ['ps', '-aq', service_name],
            stderr=False,
        ).stdout.strip()
        result = result.decode('utf-8')
        if '\n' in result:
            raise AssertionError(
                f'There is more than one container running with name {service_name}'
            )
        if not result:
            raise NoSuchService(service_name)
        return result

    @classmethod
    def _docker_compose_options(cls) -> list[str]:
        root_dir = Path(cls.assets_root)
        options = [
            '--ansi',
            'never',
            '--project-name',
            cls.service + '_' + cls.asset,
            '--file',
            str(root_dir / 'docker-compose.yml'),
            '--file',
            str(root_dir / f'docker-compose.{cls.asset}.override.yml'),
        ]
        extra = os.getenv("WAZO_TEST_DOCKER_OVERRIDE_EXTRA")
        if extra:
            options.extend(["--file", extra])
        return options

    @classmethod
    def _maybe_dump_docker_logs(cls) -> None:
        if os.getenv('WAZO_TEST_DOCKER_LOGS_ENABLED', '0') == '1':
            filename_prefix = f'{cls.__module__}.{cls.__name__}-'
            with tempfile.NamedTemporaryFile(
                dir=cls.get_log_directory(), prefix=filename_prefix, delete=False
            ) as logfile:
                cls.log_containers_to_file(logfile)
            logger.debug('Container logs dumped to %s', logfile.name)

    @classmethod
    def _maybe_collect_coverage(cls) -> None:
        if cls._is_coverage_enabled():
            file_name = f'{cls.__module__}.{cls.__name__}.coverage'
            directory = cls.get_coverage_directory()
            file_path = os.path.join(directory, file_name)
            cls.docker_copy_from_container('/tmp/coverage', file_path, cls.service)
            logger.debug(
                'Coverage file from service %s dumped to %s', cls.service, file_path
            )

    @classmethod
    def mark_logs_test_start(cls, test_name: str) -> None:
        cls._mark_logs(f'TEST START: {test_name}')

    @classmethod
    def mark_logs_test_end(cls, test_name: str) -> None:
        cls._mark_logs(f'TEST END: {test_name}')

    @classmethod
    def _mark_logs(cls, marker: str) -> None:
        cls.docker_exec(
            [
                '/bin/bash',
                '-c',
                '(date +"%F %T.%N " | tr -d "\n" &&'
                f'echo ============= {marker} ================= ) &> /proc/1/fd/1',
            ],
            privileged=True,
        )

    @staticmethod
    def get_log_directory() -> str:
        if not AssetLaunchingTestCase.log_dir:
            random_strings = "".join(
                random.choice(string.ascii_lowercase) for _ in range(8)
            )
            AssetLaunchingTestCase.log_dir = os.getenv(
                'WAZO_TEST_DOCKER_LOGS_DIR', f'/tmp/wazo-integration-{random_strings}'
            )
            if not os.path.exists(AssetLaunchingTestCase.log_dir):
                os.makedirs(AssetLaunchingTestCase.log_dir, mode=0o755)
        return str(AssetLaunchingTestCase.log_dir)

    @staticmethod
    def _is_coverage_enabled() -> bool:
        return os.getenv('WAZO_TEST_COVERAGE_ENABLED', '0') == '1'

    @staticmethod
    def get_coverage_directory() -> str:
        coverage_dir = os.environ['WAZO_TEST_COVERAGE_DIR']
        if not os.path.exists(coverage_dir):
            os.makedirs(coverage_dir, mode=0o755)
        return str(coverage_dir)


class AssetLaunchingTestCase(AbstractAssetLaunchingHelper, unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.launch_service_with_asset()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.stop_service_with_asset()


def make_asset_fixture(
    asset_class: type[AbstractAssetLaunchingHelper],
) -> Generator[type[AbstractAssetLaunchingHelper], None, None]:
    """
    Helper to create asset loading fixtures for Pytest in conftest.py or test files.

    Usage:
    ```python
    class MyAssetClass(AbstractAssetLaunchingHelper):
        assets_root = Path(__file__).parent / '..' / '..' / 'assets'
        asset = 'asset-name'
        service = 'my-service'

    @pytest.fixture(scope='session')  # session avoids recreating between different files
    def my_asset_name_asset():
        yield from make_asset_fixture(MyAssetClass)

    # For test methods
    def test_my_test(my_asset_name_asset: MyAssetClass) -> None:
        asset_name_asset.service_status()  # Containers are up, and you can call methods on

    # For whole classes:
    @pytest.mark.usefixtures('my_asset_name_asset')
    class TestExample(TestCase):
        def test_my_test(self) -> None:
            self.asset_name_asset.service_status()  # Containers are up, and you can call methods
    """
    if (
        not issubclass(asset_class, AbstractAssetLaunchingHelper)
        or asset_class is AbstractAssetLaunchingHelper
    ):
        raise TypeError(
            'You must subclass `AbstractAssetLaunchingHelper` and pass that class instead.'
        )
    asset_class.launch_service_with_asset()
    try:
        yield asset_class
    finally:
        asset_class.stop_service_with_asset()


def _run_cmd(cmd: list[str], stderr: bool = True) -> subprocess.CompletedProcess:
    logger.debug('%s', cmd)
    error_output = subprocess.STDOUT if stderr else None
    completed_process = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=error_output)

    if completed_process.stdout:
        for line in str(completed_process.stdout).replace('\\r', '').split('\\n'):
            logger.info('stdout: %s', line)
    if completed_process.stderr:
        for line in str(completed_process.stderr).replace('\\r', '').split('\\n'):
            logger.debug('stderr: %s', line)
    return completed_process
