# -*- coding: utf-8 -*-
# Copyright (C) 2015-2016 The Wazo Authors  (see AUTHORS file)
# SPDX-License-Identifier: GPL-3.0+

import uuid

from kombu import Connection
from kombu import Consumer
from kombu import Exchange
from kombu import Producer
from kombu import Queue
from kombu.exceptions import TimeoutError

BUS_EXCHANGE_XIVO = Exchange('xivo', type='topic')


class BusClient(object):

    def __init__(self, url):
        self._url = url

    @classmethod
    def from_connection_fields(cls, user='guest', password='guest', host='localhost', port=5672):
        url = 'amqp://{user}:{password}@{host}:{port}//'.format(user=user, password=password, host=host, port=port)
        return cls(url)

    def is_up(self):
        try:
            with Connection(self._url) as connection:
                producer = Producer(connection, exchange=BUS_EXCHANGE_XIVO, auto_declare=True)
                producer.publish('', routing_key='test')
        except IOError:
            return False
        else:
            return True

    def accumulator(self, routing_key, exchange=BUS_EXCHANGE_XIVO):
        queue_name = str(uuid.uuid4())
        with Connection(self._url) as conn:
            queue = Queue(name=queue_name, exchange=exchange, routing_key=routing_key, channel=conn.channel())
            queue.declare()
            queue.purge()
            accumulator = BusMessageAccumulator(self._url, queue)
        return accumulator


class BusMessageAccumulator(object):

    def __init__(self, url, queue):
        self._url = url
        self._queue = queue
        self._events = []

    def accumulate(self):
        with Connection(self._url) as conn:
            with Consumer(conn, self._queue, callbacks=[self._on_event]):
                try:
                    while True:
                        conn.drain_events(timeout=0.5)
                except TimeoutError:
                    pass

        return self._events

    def _on_event(self, body, message):
        # events are already decoded, thanks to the content-type
        self._events.append(body)
        message.ack()
