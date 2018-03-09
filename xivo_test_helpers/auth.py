# Copyright (C) 2017 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0+

import logging
import requests
import uuid

logger = logging.getLogger(__name__)


class AuthClient(object):

    def __init__(self, host, port):
        self.host = host
        self.port = port

    def url(self, *parts):
        return 'https://{host}:{port}/{path}'.format(host=self.host,
                                                     port=self.port,
                                                     path='/'.join(parts))

    def is_up(self):
        url = self.url()
        try:
            response = requests.get(url, verify=False)
            return response.status_code == 404
        except requests.RequestException as e:
            logger.debug(e)
            return False

    def set_token(self, token):
        url = self.url('_set_token')
        requests.post(url, json=token.to_dict(), verify=False)

    def revoke_token(self, token_id):
        url = self.url('_remove_token', token_id)
        requests.delete(url, verify=False)


class MockUserToken(object):

    def __init__(self, token, user_uuid, wazo_uuid=None):
        self._token = token
        self._auth_id = user_uuid
        self._wazo_uuid = wazo_uuid or str(uuid.uuid4())

    def to_dict(self):
        return {
            'token': self._token,
            'auth_id': self._auth_id,
            'xivo_uuid': self._wazo_uuid,
        }
