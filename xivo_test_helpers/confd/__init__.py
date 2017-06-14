# -*- coding: utf-8 -*-
#
# Copyright 2014-2017 The Wazo Authors  (see AUTHORS file)
# SPDX-License-Identifier: GPL-3.0+

import os

from .client import ConfdClient
from .config import confd_host, confd_port, confd_https
from .provd import create_helper as create_provd_helper
from .database import create_helper as create_database_helper


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


class SingletonProxy(object):

    def __init__(self, func, *args, **kwargs):
        self.func = func
        self.func_args = args
        self.func_kwargs = kwargs
        self.obj = None

    def __getattr__(self, name):
        if self.obj is None:
            self.obj = self.func(*self.func_args, **self.func_kwargs)
        return getattr(self.obj, name)

    def __call__(self, *args, **kwargs):
        if self.obj is None:
            self.obj = self.func(*self.func_args, **self.func_kwargs)
        return self.obj(*args, **kwargs)


confd = SingletonProxy(new_confd)
provd = SingletonProxy(create_provd_helper)
db = SingletonProxy(create_database_helper)
