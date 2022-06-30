# Copyright 2017-2022 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

import unittest

from app import app


class TestPost(unittest.TestCase):
    def test_post(self):

        self.test_app = app.test_client()

        response = self.test_app.get('/', content_type='html/text')
        self.assertEqual(response.status_code, 200)

if __name__ == '__main__':
    unittest.main()
