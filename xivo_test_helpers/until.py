# -*- coding: utf-8 -*-

# Copyright (C) 2015 Avencall
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>

import logging
import time

logger = logging.getLogger(__name__)


class NoMoreTries(Exception):
    pass


def assert_(assert_function, *args, **kwargs):
    """Run <assert_function> <tries> times, spaced with <interval> seconds. Stops
    when <function> does not throw AssertionError.

    Useful for waiting until an assert is True (or assert_that from hamcrest).

    Arguments:

        - assert_function: the function making the assertion
        - message: the message raised if <function> does not return something
          after <tries> times
        - tries: the number of times to run <function> (default: 1)
        - interval: the seconds between 2 tries (default: 1)
    """
    message = kwargs.pop('message', None)
    tries = kwargs.pop('tries', 1)
    interval = kwargs.pop('interval', 1)
    errors = []

    for _ in xrange(tries):
        try:
            assert_function(*args, **kwargs)
            return
        except AssertionError as e:
            errors.append(unicode(e))
            time.sleep(interval)
    else:
        if message:
            raise NoMoreTries(message)
        raise NoMoreTries('\n'.join(errors))


def true(function, *args, **kwargs):
    """Run <function> <tries> times, spaced with 1 second. Stops when <function>
    returns an object evaluating to True, and returns it.

    Useful for waiting for an event.

    Arguments:

        - function: the function detecting the event
        - message: the message raised if <function> does not return something
          after <tries> times
        - tries: the number of times to run <function> (default: 1)
        - interval: the seconds between 2 tries (default: 1)
    """

    message = kwargs.pop('message', None)
    tries = kwargs.pop('tries', 1)
    interval = kwargs.pop('interval', 1)
    return_value = False

    for _ in xrange(tries):
        return_value = function(*args, **kwargs)
        if return_value:
            return return_value
        time.sleep(interval)
    else:
        raise NoMoreTries(message)


def false(function, *args, **kwargs):
    """Run <function> <tries> times, spaced with 1 second. Stops when <function>
    returns an object evaluating to False, and returns it.

    Useful for waiting for an event.

    Arguments:

        - function: the function detecting the event
        - message: the message raised if <function> does not return something
          after <tries> times
        - tries: the number of times to run <function> (default: 1)
        - interval: the seconds between 2 tries (default: 1)
    """

    message = kwargs.pop('message', None)
    tries = kwargs.pop('tries', 1)
    interval = kwargs.pop('interval', 1)
    return_value = False

    for _ in xrange(tries):
        return_value = function(*args, **kwargs)
        if not return_value:
            return return_value
        time.sleep(interval)
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
        - timeout: maximum number of seconds to run <function>
        - interval: the seconds between 2 runs of <function> (default: 1)

    """

    timeout = kwargs.pop('timeout')
    interval = kwargs.pop('interval')
    message = kwargs.pop('message', None)
    return_value = False

    def executions():
        start_time = time.time()
        time_spent = interval / 10  # schedule the first execution a bit later, because start_time is now in the past
        while time_spent < timeout:
            yield start_time + time_spent
            time_spent += interval

    for next_execution in executions():
        if time.time() > next_execution:
            logger.debug('Execution of %s skipped', function)
            continue

        delay = next_execution - time.time()
        time.sleep(delay)

        try:
            return function(*args, **kwargs)
        except Exception as e:
            logger.debug('Exception caught while waiting for %s to return', function, exc_info=True)
    else:
        raise NoMoreTries(message)
