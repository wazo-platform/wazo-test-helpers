# -*- coding: utf-8 -*-
#
# Copyright 2014-2017 The Wazo Authors  (see AUTHORS file)
# SPDX-License-Identifier: GPL-3.0+

from .setup import new_confd
from .provd import create_helper as create_provd_helper
from .database import create_helper as create_database_helper


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
