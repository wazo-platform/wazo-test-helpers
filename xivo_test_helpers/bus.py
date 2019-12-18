# Copyright 2015-2018 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

import uuid

from kombu import (
    Connection,
    Consumer,
    Exchange,
    Producer,
    Queue,
)
from kombu.exceptions import TimeoutError


class BusClient(object):

    def __init__(self, url, exchange):
        self._url = url
        self._default_exchange = exchange

    @classmethod
    def from_connection_fields(cls, user='guest', password='guest', host='localhost', port=5672, exchange_name='xivo'):
        url = 'amqp://{user}:{password}@{host}:{port}//'.format(user=user, password=password, host=host, port=port)
        exchange = Exchange(exchange_name, type='topic')
        return cls(url, exchange)

    def is_up(self):
        try:
            with Connection(self._url) as connection:
                producer = Producer(connection, exchange=self._default_exchange, auto_declare=True)
                producer.publish('', routing_key='test')
        except IOError:
            return False
        else:
            return True

    def accumulator(self, routing_key, exchange=None):
        exchange = exchange or self._default_exchange
        queue_name = 'test-{}'.format(str(uuid.uuid4()))
        with Connection(self._url) as conn:
            queue = Queue(name=queue_name, exchange=exchange, routing_key=routing_key, channel=conn.channel())
            queue.declare()
            queue.purge()
            accumulator = BusMessageAccumulator(self._url, queue)
        return accumulator

    def publish(self, payload, routing_key, headers=None, exchange=None):
        exchange = exchange or self._default_exchange
        headers = headers or {}
        with Connection(self._url) as connection:
            producer = Producer(connection, exchange=exchange, auto_declare=True)
            producer.publish(payload, routing_key=routing_key, headers=headers)

    def queue_declare(self, queue):
        with Connection(self._url) as connection:
            channel = connection.default_channel
            queue.bind(channel).declare()


class BusMessageAccumulator(object):

    def __init__(self, url, queue):
        self._url = url
        self._queue = queue
        self._events = []

    def accumulate(self):
        self._pull_events()
        return self._events

    def pop(self):
        self._pull_events()
        return self._events.pop(0)

    def push_back(self, event):
        self._events.insert(0, event)

    def reset(self):
        self._pull_events()
        self._events = []

    def _pull_events(self):
        with Connection(self._url) as conn:
            with Consumer(conn, self._queue, callbacks=[self._on_event]):
                try:
                    while True:
                        conn.drain_events(timeout=0.5)
                except TimeoutError:
                    pass

    def _on_event(self, body, message):
        # events are already decoded, thanks to the content-type
        self._events.append(body)
        message.ack()
