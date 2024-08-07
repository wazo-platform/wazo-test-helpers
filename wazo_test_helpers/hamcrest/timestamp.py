# Copyright 2024 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

import datetime
from typing import Any

import hamcrest.core.base_matcher
import hamcrest.core.description


class ISOTimestamp(hamcrest.core.base_matcher.BaseMatcher):
    def _matches(self, item: Any) -> bool:
        try:
            datetime.datetime.fromisoformat(item)
            return True
        except (ValueError, TypeError):
            return False

    def describe_to(self, description: hamcrest.core.description.Description) -> None:
        description.append_text('a valid iso-formatted date string')


def an_iso_timestamp() -> ISOTimestamp:
    return ISOTimestamp()
