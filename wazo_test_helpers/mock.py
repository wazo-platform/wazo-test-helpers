# Copyright 2017-2023 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

import uuid


class _UUIDMatcher:
    def __eq__(self, other):
        try:
            uuid.UUID(hex=other)
            return True
        except (ValueError, TypeError):
            return False

    def __ne__(self, other):
        return not self == other


ANY_UUID = _UUIDMatcher()
