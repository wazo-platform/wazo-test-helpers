# -*- coding: utf-8 -*-

# Copyright 2015-2017 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0+

from ..client import ConfdClient


class ConfdWrapper(object):
    def __init__(self):
        self.confd = None

    def set_confd(self, confd):
        self.confd = confd

    def __getattr__(self, attr):
        return getattr(self.confd, attr)


class NewClientWrapper(object):

    def set_config(self, host, port):
        self.host = host
        self.port = port

    def create_client(self, headers, encoder):
        return ConfdClient.from_options(host=self.host,
                                        port=self.port,
                                        headers=headers,
                                        encoder=encoder)


class DatabaseWrapper(object):
    def __init__(self):
        self.db = None

    def set_database(self, db):
        self.db = db

    def __getattr__(self, attr):
        return getattr(self.db, attr)


confd = ConfdWrapper()
new_client = NewClientWrapper()
db = DatabaseWrapper()


def setup_confd(confd_):
    confd.set_confd(confd_.url)


def setup_new_client(host, port):
    new_client.set_config(host, port)


def setup_database(database):
    db.set_database(database)


import destination

import agent
import agent_login_status
import call_filter
import call_filter_entity
import call_log
import call_permission
import call_pickup
import call_pickup_entity
import conference
import conference_extension
import context_entity
import cti_profile
import device
import endpoint_custom
import endpoint_sccp
import endpoint_sip
import entity
import extension
import funckey_template
import group
import group_extension
import group_member_user
import incall
import incall_extension
import incall_schedule
import incall_user
import ivr
import line
import line_device
import line_endpoint_custom
import line_endpoint_sccp
import line_endpoint_sip
import line_extension
import line_sip
import meetme
import moh
import paging
import paging_caller_user
import paging_member_user
import parking_lot
import parking_lot_extension
import outcall
import outcall_extension
import outcall_trunk
import queue
import queue_extension
import queue_member_agent
import schedule
import schedule_entity
import switchboard
import switchboard_member_user
import trunk
import trunk_endpoint_custom
import trunk_endpoint_sip
import user
import user_agent
import user_call_permission
import user_cti_profile
import user_entity
import user_funckey_template
import user_import
import user_line
import user_voicemail
import voicemail
