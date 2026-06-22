#!/usr/bin/env python3
# Copyright 2015-2026 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

from setuptools import find_packages, setup

VERSION = '1.0.0'

setup(
    name='wazo-test-helpers',
    version=VERSION,
    description='Wazo test helpers',
    author='Wazo Authors',
    author_email='dev@wazo.community',
    url='http://wazo.community',
    packages=find_packages(),
    install_requires=[
        'docker',
        'requests<2.30',  # Avoid to break docker library
    ],
    extras_require={
        'pytest': ['pytest'],  # for wazo_test_helpers.pytest_asset
    },
    download_url=f'https://github.com/wazo-platform/wazo-test-helpers/tarball/{VERSION}',
)
