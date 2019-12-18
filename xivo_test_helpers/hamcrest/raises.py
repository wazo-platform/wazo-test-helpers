# Copyright 2011 hamcrest.org
# SPDX-License-Identifier: BSD-3-Clause

# Copyright 2017 The Wazo Authors  (see AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

# Derived from https://github.com/hamcrest/PyHamcrest/blob/master/src/hamcrest/core/core/raises.py

from weakref import ref
import sys
import six
from hamcrest.core.base_matcher import BaseMatcher
from hamcrest.core.compat import is_callable

__author__ = "Per Fagrell"
__copyright__ = "Copyright 2013 hamcrest.org"
__license__ = "SPDX-License-Identifier: BSD-3-Clause"


class Raises(BaseMatcher):
    def __init__(self, expected, matcher=None):
        self.matcher = matcher
        self.expected = expected
        self.actual = None
        self.function = None

    def matching(self, matcher):
        self.matcher = matcher
        return self

    def _matches(self, function):
        if not is_callable(function):
            return False

        self.function = ref(function)
        return self._call_function(function)

    def _call_function(self, function):
        self.actual = None
        try:
            function()
        except Exception:
            self.actual = sys.exc_info()[1]

            if isinstance(self.actual, self.expected):
                if self.matcher is not None:
                    return self.matcher.matches(self.actual)
                return True
        return False

    def describe_to(self, description):
        description.append_text('Expected a callable raising %s' % self.expected)

    def describe_mismatch(self, item, description):
        if not is_callable(item):
            description.append_text('%s is not callable' % item)
            return

        function = None if self.function is None else self.function()
        if function is None or function is not item:
            self.function = ref(item)
            if not self._call_function(item):
                return

        if self.actual is None:
            description.append_text('No exception raised.')
        elif isinstance(self.actual, self.expected) and self.matcher is not None:
            description.append_text('Exception did not match ')
            description.append_description_of(self.matcher) \
                       .append_text(' because ')
            self.matcher.describe_mismatch(self.actual, description)
        else:
            description.append_text('%s was raised instead: %s' % (type(self.actual), six.text_type(self.actual)))


def raises(exception, matcher=None):
    """Matches if the called function raised the expected exception.
    :param exception:  The class of the expected exception
    :param matcher:    Optional regular expression to match exception message.
    Expects the actual to be wrapped by using :py:func:`~hamcrest.core.core.raises.calling`,
    or a callable taking no arguments.
    Optional argument matcher should be a hamcrest matcher.  If provided,
    the actual exception object must match the matcher.
    Examples::
        assert_that(calling(int).with_args('q'), raises(TypeError))
        assert_that(calling(parse, broken_input), raises(ValueError, has_property('input', 'brokn')))
    """

    return Raises(exception, matcher)
