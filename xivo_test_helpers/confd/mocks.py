# -*- coding: utf-8 -*-
#
# Copyright 2015-2017 The Wazo Authors  (see AUTHORS file)
# SPDX-License-Identifier: GPL-3.0+

from wrappers import IsolatedAction

from test_api.setup import setup_sysconfd, setup_provd


class sysconfd(IsolatedAction):

    actions = {'generate': setup_sysconfd}


class provd(IsolatedAction):

    actions = {'generate': setup_provd}
