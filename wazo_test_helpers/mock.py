# Copyright 2017-2024 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

import uuid
from typing import Any


class _UUIDMatcher:
    def __eq__(self, other: str | Any) -> bool:
        try:
            uuid.UUID(hex=other)
            return True
        except (ValueError, TypeError):
            return False

    def __ne__(self, other: str | Any) -> bool:
        return not self == other


ANY_UUID = _UUIDMatcher()
