# -*- coding: utf-8 -*-

# Copyright 2015-2017 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0+

import os

CONTEXT = 'default'
INCALL_CONTEXT = 'from-extern'
OUTCALL_CONTEXT = 'to-extern'
EXTENSION_RANGE = range(1000, 5001)
ENTITY_NAME = 'xivotest'


def confd_host():
    return os.environ.get('HOST', 'localhost')


def confd_port():
    return int(os.environ.get('PORT', 9486))


def confd_https():
    return os.environ.get('HTTPS', '1') == '1'


def confd_base_url(host=None, port=None, https=None):
    if host is None:
        host = confd_host()
    if port is None:
        port = confd_port()
    if https is None:
        https = confd_https()
    scheme = 'https' if https else 'http'
    return '{}://{}:{}/1.1'.format(scheme, host, port)
