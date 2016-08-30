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

import time


class NoMoreTries(Exception):
    pass


def assert_(assert_function, *args, **kwargs):
    """Run <assert_function> <tries> times, spaced with 1 second. Stops when
    <function> does not throw AssertionError.

    Useful for waiting until an assert is True (or assert_that from hamcrest).

    Arguments:

        - assert_function: the function making the assertion
        - tries: the number of times to run <function>
    """
    tries = kwargs.pop('tries', 1)
    errors = []

    for _ in xrange(tries):
        try:
            assert_function(*args, **kwargs)
            return
        except AssertionError as e:
            errors.append(unicode(e))
            time.sleep(1)
    else:
        raise NoMoreTries('\n'.join(errors))


def true(function, *args, **kwargs):
    """Run <function> <tries> times, spaced with 1 second. Stops when <function>
    returns an object evaluating to True, and returns it.

    Useful for waiting for an event.

    Arguments:

        - function: the function detecting the event
        - message: the message raised if <function> does not return something
          after <tries> times
        - tries: the number of times to run <function>
    """

    message = kwargs.pop('message', None)
    tries = kwargs.pop('tries', 1)
    return_value = False

    for _ in xrange(tries):
        return_value = function(*args, **kwargs)
        if return_value:
            return return_value
        time.sleep(1)
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
        - tries: the number of times to run <function>
    """

    message = kwargs.pop('message', None)
    tries = kwargs.pop('tries', 1)
    return_value = False

    for _ in xrange(tries):
        return_value = function(*args, **kwargs)
        if not return_value:
            return return_value
        time.sleep(1)
    else:
        raise NoMoreTries(message)
