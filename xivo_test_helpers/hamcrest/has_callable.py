# -*- coding: utf-8 -*-
# Copyright 2011 hamcrest.org
# SPDX-License-Identifier: BSD-3-Clause

# Copyright 2018 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

# Derived from https://github.com/hamcrest/PyHamcrest/blob/master/src/hamcrest/library/object/hasproperty.py

from hamcrest.core.base_matcher import BaseMatcher
from hamcrest.core import anything
from hamcrest.core.string_description import StringDescription
from hamcrest.core.helpers.wrap_matcher import wrap_matcher as wrap_shortcut

__author__ = "Chris Rose"
__copyright__ = "Copyright 2011 hamcrest.org"
__license__ = "BSD, see License.txt"


class IsObjectWithCallable(BaseMatcher):

    def __init__(self, callable_name, value_matcher):
        self.callable_name = callable_name
        self.value_matcher = value_matcher

    def _matches(self, o):
        if o is None:
            return False

        if not hasattr(o, self.callable_name):
            return False

        value = getattr(o, self.callable_name)()
        return self.value_matcher.matches(value)

    def describe_to(self, description):
        description.append_text("an object with a callable '") \
                                        .append_text(self.callable_name) \
                                        .append_text("' matching ") \
                                        .append_description_of(self.value_matcher)

    def describe_mismatch(self, item, mismatch_description):
        if item is None:
            mismatch_description.append_text('was None')
            return

        if not hasattr(item, self.callable_name):
            mismatch_description.append_description_of(item) \
                                .append_text(' did not have the ') \
                                .append_description_of(self.callable_name) \
                                .append_text(' callable')
            return

        mismatch_description.append_text('callable ') \
                            .append_description_of(self.callable_name) \
                            .append_text(' ')
        value = getattr(item, self.callable_name)()
        self.value_matcher.describe_mismatch(value, mismatch_description)

    def __str__(self):
        d = StringDescription()
        self.describe_to(d)
        return str(d)


def has_callable(name, match=None):
    """Matches if object has a callable with a given name whose value satisfies
    a given matcher.
    :param name: The name of the callable.
    :param match: Optional matcher to satisfy.
    This matcher determines if the evaluated object has a callable with a given
    name. If no such callable is found, ``has_callable`` is not satisfied.
    If the callable is found, its value is passed to a given matcher for
    evaluation. If the ``match`` argument is not a matcher, it is implicitly
    wrapped in an :py:func:`~hamcrest.core.core.isequal.equal_to` matcher to
    check for equality.
    If the ``match`` argument is not provided, the
    :py:func:`~hamcrest.core.core.isanything.anything` matcher is used so that
    ``has_callable`` is satisfied if a matching callable is found.
    Examples::
        has_callable('__str__', starts_with('J'))
        has_callable('__str__', 'Jon')
        has_callable('__str__')
    """

    if match is None:
        match = anything()

    return IsObjectWithCallable(name, wrap_shortcut(match))
