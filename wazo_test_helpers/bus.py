# Copyright 2015-2022 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

import uuid

from kombu import Connection, Consumer, Exchange, Producer, Queue
from kombu.exceptions import OperationalError, TimeoutError


class BusClient:

    def __init__(self, url, exchange):
        self._url = url
        self._default_exchange = exchange

    @classmethod
    def from_connection_fields(cls, user='guest', password='guest', host='localhost', port=5672, exchange_name='xivo', exchange_type='topic'):
        url = 'amqp://{user}:{password}@{host}:{port}//'.format(user=user, password=password, host=host, port=port)
        exchange = Exchange(exchange_name, type=exchange_type)
        return cls(url, exchange)

    def is_up(self):
        try:
            with Connection(self._url) as connection:
                producer = Producer(connection, exchange=self._default_exchange, auto_declare=True)
                producer.publish('', routing_key='test')
        except (IOError, OperationalError):
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

    def publish(self, payload, routing_key=None, headers=None, exchange=None):
        exchange = exchange or self._default_exchange
        headers = headers or {}
        with Connection(self._url) as connection:
            producer = Producer(connection, exchange=exchange, auto_declare=True)
            producer.publish(payload, routing_key=routing_key, headers=headers)

    def queue_declare(self, queue):
        with Connection(self._url) as connection:
            channel = connection.default_channel
            queue.bind(channel).declare()

    def downstream_exchange_declare(self, name, type_, upstream=None):
        if not upstream:
            upstream = self._default_exchange
        with Connection(self._url) as connection:
            channel = connection.default_channel
            exchange = Exchange(name, type_).bind(channel)
            exchange.declare()
            upstream.bind(channel).declare()
            exchange.bind_to(upstream, routing_key='#')


class BusMessageAccumulator:

    def __init__(self, url, queue):
        self._url = url
        self._queue = queue
        self._events = []

    # FIXME: Clean with_headers after routing_key -> headers migration
    def accumulate(self, with_headers=False):
        self._pull_events()
        if with_headers:
            return [
                {'message': message, 'headers': headers}
                for message, headers in self._events
            ]
        return [message for message, _ in self._events]

    # FIXME: Clean with_headers after routing_key -> headers migration
    def pop(self, with_headers=False):
        self._pull_events()
        message, headers = self._events.pop(0)
        if with_headers:
            return {'message': message, 'headers': headers}
        return message

    def push_back(self, event, headers=None):
        self._events.insert(0, (event, headers))

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
        self._events.append((body, message.headers))
        message.ack()
