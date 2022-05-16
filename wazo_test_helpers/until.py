# Copyright 2015-2022 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

import logging
import time

from functools import partial

logger = logging.getLogger(__name__)


class NoMoreTries(Exception):
    pass


def tries_executions(tries, interval):
    for _ in range(tries):
        yield
        time.sleep(interval)


def timeout_executions(timeout, interval):
    end_time = time.time() + timeout
    while time.time() < end_time:
        yield
        time_left = end_time - time.time()
        delay = time_left % interval
        time.sleep(delay)


def assert_(assert_function, *args, **kwargs):
    """Run <assert_function> <tries> times, spaced with <interval> seconds. Stops
    when <function> does not throw AssertionError.

    Useful for waiting until an assert is True (or assert_that from hamcrest).

    Arguments:

        - assert_function: the function making the assertion
        - message: the message raised if <function> does not return something
          after <tries> times
        - timeout: the amount of seconds to try running <function>. Overrides `tries`.
        - tries: the number of times to run <function> (default: 1). Overriden by `timeout`.
        - interval: the seconds between 2 tries (default: 1)
    """

    message = kwargs.pop('message', None)
    tries = kwargs.pop('tries', 1)
    timeout = kwargs.pop('timeout', None)
    interval = kwargs.pop('interval', 1)
    errors = []

    if timeout:
        executions = partial(timeout_executions, timeout, interval)
    else:
        executions = partial(tries_executions, tries, interval)

    for _ in executions():
        try:
            assert_function(*args, **kwargs)
            return
        except AssertionError as e:
            errors.append(str(e))
    else:
        error_message = '\n'.join(errors)
        if message:
            error_message = message + '\n' + error_message
        raise AssertionError(error_message)


def true(function, *args, **kwargs):
    """Run <function> <tries> times, spaced with 1 second. Stops when <function>
    returns an object evaluating to True, and returns it.

    Useful for waiting for an event.

    Arguments:

        - function: the function detecting the event
        - message: the message raised if <function> does not return something
          after <tries> times
        - timeout: the amount of seconds to try running <function>. Overrides `tries`.
        - tries: the number of times to run <function> (default: 1). Overriden by `timeout`.
        - interval: the seconds between 2 tries (default: 1)
    """

    message = kwargs.pop('message', None)
    timeout = kwargs.pop('timeout', None)
    tries = kwargs.pop('tries', 1)
    interval = kwargs.pop('interval', 1)
    return_value = False

    if timeout:
        executions = partial(timeout_executions, timeout, interval)
    else:
        executions = partial(tries_executions, tries, interval)

    for _ in executions():
        return_value = function(*args, **kwargs)
        if return_value:
            return return_value
    else:
        raise NoMoreTries(message)


def false(function, *args, **kwargs):
    """Run <function> <tries> times, spaced with <interval> seconds. Stops when
    <function> returns an object evaluating to False, and returns it.

    Useful for waiting for an event.

    Arguments:

        - function: the function detecting the event
        - message: the message raised if <function> does not return something
          after <tries> times
        - timeout: the amount of seconds to try running <function>. Overrides `tries`.
        - tries: the number of times to run <function> (default: 1). Overriden by `timeout`.
        - interval: the seconds between 2 tries (default: 1)

    """

    message = kwargs.pop('message', None)
    timeout = kwargs.pop('timeout', None)
    tries = kwargs.pop('tries', 1)
    interval = kwargs.pop('interval', 1)
    return_value = False

    if timeout:
        executions = partial(timeout_executions, timeout, interval)
    else:
        executions = partial(tries_executions, tries, interval)

    for _ in executions():
        return_value = function(*args, **kwargs)
        if not return_value:
            return return_value
    else:
        raise NoMoreTries(message)


def return_(function, *args, **kwargs):
    """Periodically run <function> for <timeout> seconds, spaced with <interval>
    seconds. Stops when <function> returns something, then return this value.

    Useful for waiting for a function that throws an exception when not ready.

    Arguments:

        - function: the function detecting the event
        - message: the message raised if <function> does not return something
          after <timeout> seconds
        - timeout: the amount of seconds to try running <function>.
        - interval: the seconds between 2 runs of <function> (default: 1)

    """

    timeout = kwargs.pop('timeout')
    interval = kwargs.pop('interval', 1)
    message = kwargs.pop('message', None)
    errors = []

    for _ in timeout_executions(timeout, interval):
        try:
            return function(*args, **kwargs)
        except Exception as e:
            errors.append(str(e))
    else:
        error_message = '\n'.join(errors)
        if message:
            error_message = message + '\n' + error_message
        raise NoMoreTries(error_message)
