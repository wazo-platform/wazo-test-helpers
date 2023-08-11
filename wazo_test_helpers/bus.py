# Copyright 2015-2023 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later
from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, TypedDict, Any

from kombu import binding, Connection, Consumer, Exchange, Producer, Queue, Message
from kombu.exceptions import OperationalError, TimeoutError
from wazo_test_helpers import until

if TYPE_CHECKING:
    from hamcrest.core.matcher import Matcher


class MessageWithHeadersDict(TypedDict):
    message: Message
    headers: dict | None


class BusClient:
    def __init__(self, url: str, exchange: Exchange) -> None:
        self._url = url
        self._default_exchange = exchange

    @classmethod
    def from_connection_fields(
        cls,
        user: str = 'guest',
        password: str = 'guest',
        host: str = 'localhost',
        port: int = 5672,
        exchange_name: str = 'xivo',
        exchange_type: str = 'topic',
    ) -> BusClient:
        url = f'amqp://{user}:{password}@{host}:{port}//'
        exchange = Exchange(exchange_name, type=exchange_type)
        return cls(url, exchange)

    def is_up(self) -> bool:
        try:
            with Connection(self._url) as connection:
                producer = Producer(
                    connection, exchange=self._default_exchange, auto_declare=True
                )
                producer.publish('', routing_key='test')
        except (OSError, OperationalError):
            return False
        return True

    def accumulator(
        self,
        routing_key: str | None = None,
        exchange: Exchange | None = None,
        headers: dict | None = None,
    ) -> BusMessageAccumulator:
        exchange = exchange or self._default_exchange
        queue_name = f'test-{str(uuid.uuid4())}'
        with Connection(self._url) as conn:
            if routing_key:
                queue = Queue(
                    name=queue_name,
                    exchange=exchange,
                    routing_key=routing_key,
                    channel=conn.channel(),
                )
            elif headers:
                queue = Queue(
                    name=queue_name,
                    exchange=exchange,
                    bindings=[binding(exchange=exchange, arguments=headers)],
                    channel=conn.channel(),
                )
            else:
                raise Exception('Need a routing key or a header')
            queue.declare()
            queue.purge()
            accumulator = BusMessageAccumulator(self._url, queue)
        return accumulator

    def publish(
        self,
        payload: Any,
        routing_key: str | None = None,
        headers: dict | None = None,
        exchange: Exchange | None = None,
    ) -> None:
        exchange = exchange or self._default_exchange
        headers = headers or {}
        with Connection(self._url) as connection:
            producer = Producer(connection, exchange=exchange, auto_declare=True)
            producer.publish(payload, routing_key=routing_key, headers=headers)

    def queue_declare(self, queue: Queue) -> None:
        with Connection(self._url) as connection:
            channel = connection.default_channel
            queue.bind(channel).declare()

    # FIXME: Remove after routing_key -> headers migration
    def downstream_exchange_declare(
        self, name: str, type_: str, upstream: Exchange | None = None
    ) -> None:
        if not upstream:
            upstream = self._default_exchange
        with Connection(self._url) as connection:
            channel = connection.default_channel
            exchange = Exchange(name, type_).bind(channel)
            exchange.declare()
            upstream.bind(channel).declare()
            exchange.bind_to(upstream, routing_key='#')


class BusMessageAccumulator:
    def __init__(self, url: str, queue: Queue) -> None:
        self._url = url
        self._queue: Queue = queue
        self._events: list[tuple[Any, dict | None]] = []

    # FIXME: Clean with_headers after routing_key -> headers migration
    def accumulate(
        self, with_headers: bool = False
    ) -> list[Message | MessageWithHeadersDict]:
        self._pull_events()
        if with_headers:
            return [
                {'message': message, 'headers': headers}
                for message, headers in self._events
            ]
        return [message for message, _ in self._events]

    def until_assert_that_accumulate(
        self, matcher: Matcher, message: str | None = None, timeout: int | None = None
    ) -> None:
        # Optional dependency
        from hamcrest import assert_that

        def assert_function() -> None:
            assert_that(self.accumulate(), matcher, message or "")

        until.assert_(assert_function, timeout=timeout, message=message)

    # FIXME: Clean with_headers after routing_key -> headers migration
    def pop(self, with_headers: bool = False) -> Message | MessageWithHeadersDict:
        self._pull_events()
        message, headers = self._events.pop(0)
        if with_headers:
            return {'message': message, 'headers': headers}
        return message

    def push_back(self, event: Message, headers: dict | None = None) -> None:
        self._events.insert(0, (event, headers))

    def reset(self) -> None:
        self._pull_events()
        self._events = []

    def _pull_events(self) -> None:
        with Connection(self._url) as conn:
            with Consumer(conn, self._queue, callbacks=[self._on_event]):
                try:
                    while True:
                        conn.drain_events(timeout=0.5)
                except TimeoutError:
                    pass

    def _on_event(self, body: Any, message: Message) -> None:
        # events are already decoded, thanks to the content-type
        self._events.append((body, message.headers))
        message.ack()
