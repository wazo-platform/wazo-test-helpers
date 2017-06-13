# -*- coding: utf-8 -*-
#
# Copyright 2014-2017 The Wazo Authors  (see AUTHORS file)
# SPDX-License-Identifier: GPL-3.0+

import os

from .client import ConfdClient
from .sysconfd import SysconfdMock
from .config import confd_host, confd_port, confd_https
from . import provd
from . import database


def new_client(headers=None, encoder=None):
    xivo_host = confd_host()
    xivo_confd_port = confd_port()
    xivo_confd_login = os.environ.get('LOGIN', 'admin')
    xivo_confd_password = os.environ.get('PASSWORD', 'proformatique')
    xivo_https = confd_https()
    client = ConfdClient.from_options(host=xivo_host,
                                      port=xivo_confd_port,
                                      username=xivo_confd_login,
                                      password=xivo_confd_password,
                                      https=xivo_https,
                                      headers=headers,
                                      encoder=encoder)
    return client


def new_confd(headers=None):
    return new_client(headers).url


def setup_provd():
    helper = provd.create_helper()
    helper.reset()
    return helper


def setup_database():
    helper = database.create_helper()
    helper.recreate()
    return helper


def setup_sysconfd():
    url = os.environ.get('SYSCONFD_URL', 'http://localhost:18668')
    mock = SysconfdMock(url)
    mock.clear()
    return mock
