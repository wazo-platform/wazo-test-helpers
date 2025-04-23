# Copyright 2017-2025 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

import logging
import uuid
from typing import TYPE_CHECKING, Any, TypedDict

import requests

if TYPE_CHECKING:
    from wazo_auth_client.types import TokenDict, TokenMetadataDict


logger = logging.getLogger(__name__)


class CredentialsDict(TypedDict):
    username: str
    password: str


class CredentialsTokenDict(CredentialsDict, total=False):
    token: str


class TenantDict(TypedDict):
    uuid: str
    name: str
    parent_uuid: str


class UserDict(TypedDict):
    uuid: str
    firstname: str
    lastname: str


class AuthClient:
    def __init__(self, host: str, port: int) -> None:
        self.host = host
        self.port = port

    def url(self, *parts: str) -> str:
        return f'http://{self.host}:{self.port}/{"/".join(parts)}'

    def is_up(self) -> bool:
        url = self.url()
        try:
            response = requests.get(url)
            return response.status_code == 404
        except requests.RequestException as e:
            logger.debug(e)
            return False

    def reset_external_config(self) -> None:
        url = self.url('_reset_external_config')
        requests.post(url)

    def set_external_config(self, config_info: dict) -> None:
        url = self.url('_set_external_config')
        requests.post(url, json=config_info)

    def reset_external_auth(self) -> None:
        url = self.url('_reset_external_auth')
        requests.post(url)

    def set_external_auth(self, auth_info: dict) -> None:
        url = self.url('_set_external_auth')
        requests.post(url, json=auth_info)

    def reset_external_users(self) -> None:
        url = self.url('_reset_external_users')
        requests.post(url)

    def set_external_users(self, users_info: dict) -> None:
        url = self.url('_set_external_users')
        requests.post(url, json=users_info)

    def set_tenants(self, *tenants: TenantDict) -> None:
        url = self.url('_set_tenants')
        requests.post(url, json=tenants)

    def set_users(self, *users: UserDict) -> None:
        url = self.url('_set_users')
        requests.post(url, json=users)

    def set_sessions(self, *sessions: dict) -> None:
        url = self.url('_set_sessions')
        requests.post(url, json=sessions)

    def set_refresh_tokens(self, *refresh_tokens: dict) -> None:
        url = self.url('_set_refresh_tokens')
        requests.post(url, json=refresh_tokens)

    def set_token(self, token: MockUserToken) -> None:
        url = self.url('_set_token')
        requests.post(url, json=token.to_dict())

    def revoke_token(self, token_id: str) -> None:
        url = self.url('_remove_token', token_id)
        requests.delete(url)

    def set_invalid_credentials(self, credentials: MockCredentials) -> None:
        url = self.url('_add_invalid_credentials')
        requests.post(url, json=credentials.to_dict())

    def set_valid_credentials(self, credentials: MockCredentials, token: str) -> None:
        url = self.url('_add_valid_credentials')
        credentials_with_token = credentials.to_dict()
        credentials_with_token['token'] = token
        requests.post(url, json=credentials_with_token)

    def set_credentials_for_invalid_token(self, credentials: MockCredentials) -> None:
        url = self.url('_add_credentials_for_invalid_token')
        requests.post(url, json=credentials.to_dict())


class MockUserToken:
    @classmethod
    def some_token(cls, **kwargs: Any) -> MockUserToken:
        kwargs.setdefault('token', str(uuid.uuid4()))
        kwargs.setdefault('user_uuid', str(uuid.uuid4()))
        return cls(**kwargs)

    def __init__(
        self,
        token: str,
        user_uuid: str,
        wazo_uuid: str | None = None,
        metadata: TokenMetadataDict | None = None,
        acl: list[str] | None = None,
        session_uuid: str | None = None,
        utc_expires_at: str | None = None,
    ) -> None:
        self.token_id = token
        self.auth_id = user_uuid
        self.wazo_uuid = wazo_uuid or str(uuid.uuid4())
        self.acl = acl
        self.session_uuid = session_uuid
        self.metadata = metadata or {}
        self.metadata.setdefault('uuid', user_uuid)
        self.utc_expires_at = utc_expires_at

    def to_dict(self) -> TokenDict:
        result = {
            'token': self.token_id,
            'auth_id': self.auth_id,
            'xivo_uuid': self.wazo_uuid,
            'session_uuid': self.session_uuid,
            'metadata': self.metadata,
            'utc_expires_at': self.utc_expires_at,
        }
        if self.acl is not None:
            result['acl'] = self.acl
        return result


class MockCredentials:
    def __init__(self, username: str, password: str) -> None:
        self.username = username
        self.password = password

    def to_dict(self) -> CredentialsTokenDict:
        return {
            'username': self.username,
            'password': self.password,
        }
