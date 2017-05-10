# -*- coding: utf-8 -*-
# Copyright 2017 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0+

import uuid


class _UUIDMatcher(object):

    def __eq__(self, other):
        try:
            uuid.UUID(hex=other)
            return True
        except (ValueError, TypeError):
            return False

    def __ne__(self, other):
        return not self == other


ANY_UUID = _UUIDMatcher()
