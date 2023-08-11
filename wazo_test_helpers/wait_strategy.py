# Copyright 2016-2023 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later
from __future__ import annotations

from collections.abc import Callable


class WaitStrategy:
    def wait(self, integration_test: Callable[..., None]) -> None:
        raise NotImplementedError()


class NoWaitStrategy(WaitStrategy):
    def wait(self, integration_test: Callable[..., None]) -> None:
        pass
