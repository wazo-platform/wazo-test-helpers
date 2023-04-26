#!/usr/bin/env python3
# Copyright 2015-2023 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

from setuptools import setup
from setuptools import find_packages

VERSION = '1.0.0'

setup(
    name='wazo-test-helpers',
    version=VERSION,

    description='Wazo test helpers',

    author='Wazo Authors',
    author_email='dev@wazo.community',

    url='http://wazo.community',

    packages=find_packages(),
    install_requires=['docker'],
    download_url=f'https://github.com/wazo-platform/wazo-test-helpers/tarball/{VERSION}',
)
