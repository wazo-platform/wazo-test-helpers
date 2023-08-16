# Copyright 2011-2023 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: BSD-3-Clause

# Copyright 2017-2021 The Wazo Authors  (see AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

# Derived from https://github.com/hamcrest/PyHamcrest/blob/master/src/hamcrest/core/core/raises.py
from __future__ import annotations

from typing import Any, TypeVar, Callable
from weakref import ref

import sys
import traceback

from hamcrest.core.base_matcher import BaseMatcher, Description

__author__ = "Per Fagrell"
__copyright__ = "Copyright 2013 hamcrest.org"
__license__ = "SPDX-License-Identifier: BSD-3-Clause"

Self = TypeVar("Self", bound="Raises")


class Raises(BaseMatcher):
    def __init__(self, expected: Any, matcher: BaseMatcher | None = None) -> None:
        self.matcher = matcher
        self.expected: Any = expected
        self.actual: Any = None
        self.function: Callable[..., Any] | None = None

    def matching(self: Self, matcher: BaseMatcher) -> Self:
        self.matcher = matcher
        return self

    def _matches(self, function: Callable[..., Any] | None) -> bool:
        if not callable(function):
            return False

        self.function = ref(function)
        return self._call_function(function)

    def _call_function(self, function: Callable[..., Any]) -> bool:
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

    def describe_to(self, description: Description) -> None:
        description.append_text(f'Expected a callable raising {self.expected}')

    def describe_mismatch(self, item: Any, description: Description) -> None:
        if not callable(item):
            description.append_text(f'{item} is not callable')
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
            description.append_description_of(self.matcher).append_text(' because ')
            self.matcher.describe_mismatch(self.actual, description)
        else:
            description.append_text(
                f'{type(self.actual)} was raised instead: {str(self.actual)}\n'
            )
            traceback_lines = traceback.format_exception(
                type(self.actual), self.actual, self.actual.__traceback__
            )
            for traceback_line in traceback_lines:
                description.append_text(traceback_line)


def raises(exception: BaseException, matcher: BaseMatcher | None = None) -> Raises:
    """Matches if the called function raised the expected exception.
    :param exception:  The class of the expected exception
    :param matcher:    Optional regular expression to match exception message.
    Expects the actual to be wrapped by using :py:func:`~hamcrest.core.core.raises.calling`,
    or a callable taking no arguments.
    Optional argument matcher should be a hamcrest matcher.  If provided,
    the actual exception object must match the matcher.
    Examples::
        assert_that(calling(int).with_args('q'), raises(TypeError))
        assert_that(
            calling(parse, broken_input),
            raises(ValueError, has_property('input', 'broken')),
        )
    """

    return Raises(exception, matcher)
