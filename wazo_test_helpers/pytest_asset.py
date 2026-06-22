# Copyright 2026 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

"""Shared pytest plugin to manage integration-test Docker assets.

Integration suites mark each test class with the asset it needs
(``@pytest.mark.usefixtures('<asset>')``). This plugin handles the asset
lifecycle so suites don't each reimplement it in their conftest:

- tests are grouped by asset so each one is launched once for a contiguous run;
- an asset is torn down as soon as the next test needs a different one, rather
  than lingering until the session ends;
- a teardown failure is recorded and reported at the end instead of aborting
  the following test's setup;
- container logs get per-test start/end markers (``mark_logs``).

A conftest activates the hooks by calling ``register`` from its own
``pytest_configure`` and declares its assets:

    from wazo_test_helpers.pytest_asset import (
        asset_fixture,
        enable_mark_logs_fixture,
        register,
    )

    from .helpers import base as asset

    def pytest_configure(config):
        register(config)

    base = asset_fixture(asset.APIAssetLaunchingTestCase)
    database = asset_fixture(asset.DBAssetLaunchingTestCase)
    mark_logs = enable_mark_logs_fixture()
"""

from __future__ import annotations

import logging
import sys
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from typing import TYPE_CHECKING, Any, Literal

import pytest

if TYPE_CHECKING:
    from wazo_test_helpers.asset_launching_test_case import AssetLaunchingTestCase

logger = logging.getLogger(__name__)

_ScopeName = Literal['session', 'package', 'module', 'class', 'function']

_teardowns: dict[str, Callable[[], None]] = {}
_teardown_failures: list[tuple[str, BaseException]] = []


def register(config: pytest.Config) -> None:
    """Activate the asset hooks; call from a conftest's ``pytest_configure``."""
    plugin_manager = config.pluginmanager
    module = sys.modules[__name__]
    if not plugin_manager.is_registered(module):
        plugin_manager.register(module)


def asset_fixture(
    asset_class: type[AssetLaunchingTestCase],
    *,
    scope: _ScopeName = 'session',
) -> Callable[[pytest.FixtureRequest], Iterator[None]]:
    """Build a session-scoped pytest fixture managing ``asset_class``'s lifecycle."""

    @pytest.fixture(scope=scope)
    def _asset(request: pytest.FixtureRequest) -> Iterator[None]:
        with _managed_asset(request, asset_class):
            yield

    return _asset


def enable_mark_logs_fixture() -> Callable[[pytest.FixtureRequest], Iterator[None]]:
    @pytest.fixture(autouse=True, scope='function')
    def mark_logs(request: pytest.FixtureRequest) -> Iterator[None]:
        cls = request.cls
        if cls is None or not hasattr(cls, 'asset_cls'):
            yield
            return
        test_name = f'{cls.__name__}.{request.function.__name__}'
        cls.asset_cls.mark_logs_test_start(test_name)
        yield
        cls.asset_cls.mark_logs_test_end(test_name)

    return mark_logs


@pytest.hookimpl
def pytest_collection_modifyitems(
    session: pytest.Session,
    config: pytest.Config,
    items: list[pytest.Item],
) -> None:
    items.sort(key=lambda item: _marker_of(item) or '')


@pytest.hookimpl(trylast=True)
def pytest_runtest_teardown(item: pytest.Item, nextitem: pytest.Item | None) -> None:
    if nextitem is None:
        return
    current = _marker_of(item)
    upcoming = _marker_of(nextitem)
    if current is not None and current != upcoming:
        try:
            _teardown(current)
        except Exception as exc:
            logger.exception('Failed to tear down asset for marker %r', current)
            _teardown_failures.append((current, exc))


@pytest.hookimpl
def pytest_terminal_summary(
    terminalreporter: Any,
    exitstatus: int,
    config: pytest.Config,
) -> None:
    for marker, exc in _teardown_failures:
        terminalreporter.write_sep(
            '!', f'Asset teardown failed for marker {marker!r}: {exc}'
        )


def _marker_of(item: Any) -> str | None:
    """Return the asset name from a test's ``usefixtures`` marker, or ``None``."""
    parent = getattr(item, 'parent', None)
    for marker in getattr(parent, 'own_markers', []):
        if marker.name == 'usefixtures' and marker.args:
            return str(marker.args[0])
    return None


def _teardown(marker: str) -> None:
    """Run and forget the teardown registered for ``marker`` (idempotent)."""
    teardown = _teardowns.get(marker)
    if teardown is not None:
        teardown()
        _teardowns.pop(marker, None)


@contextmanager
def _managed_asset(
    request: pytest.FixtureRequest,
    asset_class: type[AssetLaunchingTestCase],
) -> Iterator[None]:
    """Set up ``asset_class`` and ensure it is torn down exactly once."""
    marker = request.fixturename
    asset_class.setUpClass()
    if marker:
        _teardowns[marker] = asset_class.tearDownClass
    try:
        yield
    finally:
        if marker:
            _teardown(marker)
        else:
            asset_class.tearDownClass()
