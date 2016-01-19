#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (C) 2015-2016 Avencall
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

from setuptools import setup
from setuptools import find_packages

VERSION = '0.1.5'

setup(
    name='xivo-test-helpers',
    version=VERSION,

    description='XiVO test helpers',

    author='Avencall',
    author_email='dev@avencall.com',

    url='https://github.com/xivo-pbx/xivo-test-helpers',

    packages=find_packages(),
    install_requires=['docker-py'],
    download_url='https://github.com/xivo-pbx/xivo-test-helpers/tarball/{}'.format(VERSION),
)
