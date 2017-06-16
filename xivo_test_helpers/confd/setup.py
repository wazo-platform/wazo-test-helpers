# -*- coding: utf-8 -*-
#
# Copyright 2014-2017 The Wazo Authors  (see AUTHORS file)
# SPDX-License-Identifier: GPL-3.0+

import os

from .sysconfd import SysconfdMock
from .provd import create_helper as provd_create_helper
from .database import create_helper as database_create_helper


def setup_provd():
    helper = provd_create_helper()
    helper.reset()
    return helper


def setup_database():
    helper = database_create_helper()
    helper.recreate()
    return helper


def setup_sysconfd():
    url = os.environ.get('SYSCONFD_URL', 'http://localhost:18668')
    mock = SysconfdMock(url)
    mock.clear()
    return mock
