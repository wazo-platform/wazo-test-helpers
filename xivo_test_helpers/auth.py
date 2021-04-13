# Copyright 2017-2021 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

import logging
import uuid

import requests

logger = logging.getLogger(__name__)


class AuthClient:

    def __init__(self, host, port):
        self.host = host
        self.port = port

    def url(self, *parts):
        return 'http://{host}:{port}/{path}'.format(
            host=self.host,
            port=self.port,
            path='/'.join(parts)
        )

    def is_up(self):
        url = self.url()
        try:
            response = requests.get(url)
            return response.status_code == 404
        except requests.RequestException as e:
            logger.debug(e)
            return False

    def reset_external_config(self):
        url = self.url('_reset_external_config')
        requests.post(url)

    def set_external_config(self, config_info):
        url = self.url('_set_external_config')
        requests.post(url, json=config_info)

    def reset_external_auth(self):
        url = self.url('_reset_external_auth')
        requests.post(url)

    def set_external_auth(self, auth_info):
        url = self.url('_set_external_auth')
        requests.post(url, json=auth_info)

    def set_tenants(self, *tenants):
        url = self.url('_set_tenants')
        requests.post(url, json=tenants)

    def set_sessions(self, *sessions):
        url = self.url('_set_sessions')
        requests.post(url, json=sessions)

    def set_refresh_tokens(self, *sessions):
        url = self.url('_set_refresh_tokens')
        requests.post(url, json=sessions)

    def set_token(self, token):
        url = self.url('_set_token')
        requests.post(url, json=token.to_dict())

    def revoke_token(self, token_id):
        url = self.url('_remove_token', token_id)
        requests.delete(url)

    def set_invalid_credentials(self, credentials):
        url = self.url('_add_invalid_credentials')
        requests.post(url, json=credentials.to_dict())

    def set_valid_credentials(self, credentials, token):
        url = self.url('_add_valid_credentials')
        credentials_with_token = credentials.to_dict()
        credentials_with_token['token'] = token
        requests.post(url, json=credentials_with_token)

    def set_credentials_for_invalid_token(self, credentials):
        url = self.url('_add_credentials_for_invalid_token')
        requests.post(url, json=credentials.to_dict())


class MockUserToken:

    @classmethod
    def some_token(cls, **kwargs):
        kwargs.setdefault('token', str(uuid.uuid4()))
        kwargs.setdefault('user_uuid', str(uuid.uuid4()))
        return cls(**kwargs)

    def __init__(self, token, user_uuid, wazo_uuid=None, metadata=None, acl=None):
        self.token_id = token
        self.auth_id = user_uuid
        self.wazo_uuid = wazo_uuid or str(uuid.uuid4())
        self.acl = acl
        self.metadata = metadata or {}
        self.metadata.setdefault('uuid', user_uuid)

    def to_dict(self):
        result = {
            'token': self.token_id,
            'auth_id': self.auth_id,
            'xivo_uuid': self.wazo_uuid,
            'metadata': self.metadata,
        }
        if self.acl is not None:
            result['acl'] = self.acl
        return result


class MockCredentials:

    def __init__(self, username, password):
        self.username = username
        self.password = password

    def to_dict(self):
        return {
            'username': self.username,
            'password': self.password,
        }
