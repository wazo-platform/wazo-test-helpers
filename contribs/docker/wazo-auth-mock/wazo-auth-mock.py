#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright 2015-2021 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

import logging
import sys
import uuid

from flask import Flask, jsonify, request

logging.basicConfig(level=logging.DEBUG)

logger = logging.getLogger()

app = Flask(__name__)

port = int(sys.argv[1])
try:
    url_prefix = sys.argv[2]
except IndexError:
    url_prefix = ''

DEFAULT_POLICIES = {
    'wazo_default_admin_policy': {
        'uuid': '00000000-0000-0000-0000-000000000001',
        'name': 'wazo_default_admin_policy',
    }
}

valid_tokens = {
    'valid-token': {
        'auth_id': 'uuid',
        'token': 'valid-token',
        'metadata': {
            'uuid': 'uuid',
            'pbx_user_uuid': 'uuid',
            'tenant_uuid': 'ffffffff-ffff-ffff-ffff-ffffffffffff',
        }
    },
    'valid-token-multitenant': {
        'auth_id': 'uuid-multitenant',
        'token': 'valid-token-multitenant',
        'metadata': {
            'uuid': 'uuid-multitenant',
            'pbx_user_uuid': 'uuid-multitenant',
            'tenant_uuid': 'eeeeeeee-eeee-eeee-eeee-eeeeeeeeeee1',
        }
    },
    'valid-token-master-tenant': {
        'auth_id': 'uuid-tenant-master',
        'token': 'valid-token-master-tenant',
        'metadata': {
            'uuid': 'uuid-tenant-master',
            'pbx_user_uuid': 'uuid-tenant-master',
            'tenant_uuid': 'eeeeeeee-eeee-eeee-eeee-eeeeeeeeee10',
        }
    },
    'valid-token-sub-tenant': {
        'auth_id': 'uuid-subtenant',
        'token': 'valid-token-sub-tenant',
        'metadata': {
            'uuid': 'uuid-subtenant',
            'pbx_user_uuid': 'uuid-subtenant',
            'tenant_uuid': 'eeeeeeee-eeee-eeee-eeee-eeeeeeeeee11',
        }
    },
    'non-user-token': {
        'auth_id': 'uuid-non-user',
        'token': 'non-user-token',
        'metadata': {
            'uuid': None,
            'pbx_user_uuid': None,
            'tenant_uuid': 'dddddddd-dddd-dddd-dddd-dddddddddd11',
        }
    }
}

valid_credentials = {}
external = {}
external_config = {}
invalid_username_passwords = [('test', 'foobar')]
sessions = {}
refresh_tokens = {}
tenants = [
    {
        'uuid': 'ffffffff-ffff-ffff-ffff-ffffffffffff',
        'name': 'valid-tenant',
        'parent_uuid': 'ffffffff-ffff-ffff-ffff-ffffffffffff',
    },

    {
        'uuid': 'eeeeeeee-eeee-eeee-eeee-eeeeeeeeeee1',
        'name': 'valid-tenant1',
        'parent_uuid': 'eeeeeeee-eeee-eeee-eeee-eeeeeeeeeee1',
    },
    {
        'uuid': 'eeeeeeee-eeee-eeee-eeee-eeeeeeeeeee2',
        'name': 'valid-tenant2',
        'parent_uuid': 'eeeeeeee-eeee-eeee-eeee-eeeeeeeeeee1',
    },
    {
        'uuid': 'eeeeeeee-eeee-eeee-eeee-eeeeeeeeeee3',
        'name': 'valid-tenant3',
        'parent_uuid': 'eeeeeeee-eeee-eeee-eeee-eeeeeeeeeee1',
    },

    {
        'uuid': 'eeeeeeee-eeee-eeee-eeee-eeeeeeeeee10',
        'name': 'master-tenant',
        'parent_uuid': 'eeeeeeee-eeee-eeee-eeee-eeeeeeeeee10',
    },
    {
        'uuid': 'eeeeeeee-eeee-eeee-eeee-eeeeeeeeee11',
        'name': 'sub-tenant',
        'parent_uuid': 'eeeeeeee-eeee-eeee-eeee-eeeeeeeeee10',
    },
]
token_that_will_be_invalid_when_used = [('test', 'iddqd')]
users = {}
wrong_acl_tokens = {'invalid-acl-token'}

_requests = []


def _reset():
    global _requests
    global _tenants
    _requests = []
    _tenants = {}


@app.route(url_prefix + "/0.1/external/<external_service>/config", methods=['GET'])
def external_config_get(external_service):
    if external_service in external_config:
        return jsonify(external_config[external_service])
    else:
        return '', 404


@app.route(url_prefix + "/_reset_external_config", methods=['POST'])
def external_config_reset():
    global external_config
    external_config = {}
    return '', 204


@app.route(url_prefix + "/_set_external_config", methods=['POST'])
def external_config_set():
    global external_config
    external_config = request.get_json()
    return '', 201


@app.route(url_prefix + "/0.1/users/<user_uuid>/external/<external_service>", methods=['GET'])
def external_auth_external_service_get(user_uuid, external_service):
    if external:
        return jsonify(external)
    else:
        return '', 404


@app.route(url_prefix + "/_reset_external_auth", methods=['POST'])
def external_auth_reset():
    global external
    external = {}
    return '', 204


@app.route(url_prefix + "/_set_external_auth", methods=['POST'])
def external_auth_set():
    global external
    external = request.get_json()
    return '', 201


@app.before_request
def log_request():
    if not request.path.startswith('/_'):
        path = request.path
        log = {'method': request.method,
               'path': path,
               'query': request.args.items(multi=True),
               'body': request.data,
               'json': request.json,
               'headers': dict(request.headers)}
        _requests.append(log)


@app.after_request
def print_request_response(response):
    logger.debug('request: %s', {
        'method': request.method,
        'path': request.path,
        'query': request.args.items(multi=True),
        'body': request.data,
        'headers': dict(request.headers)
    })
    logger.debug('response: %s', {
        'body': response.data,
    })
    return response


@app.route('/0.1/_requests', methods=['GET'])
def list_requests():
    return jsonify(requests=_requests)


@app.route('/0.1/_reset', methods=['POST'])
def reset():
    _reset()
    return '', 204


@app.route(url_prefix + "/_set_tenants", methods=['POST'])
def set_tenants():
    global tenants
    new_tenants = request.get_json()
    for tenant in new_tenants:
        tenant.setdefault('name', tenant['uuid'])
        tenant.setdefault('parent_uuid', tenant['uuid'])
    tenants = new_tenants
    return '', 204


@app.route(url_prefix + "/_set_token", methods=['POST'])
def set_token():
    request_body = request.get_json()
    token = request_body['token']

    valid_tokens[token] = request_body

    return '', 204


@app.route(url_prefix + "/_set_sessions", methods=['POST'])
def set_sessions():
    global sessions
    sessions = request.get_json()
    return '', 204


@app.route(url_prefix + "/_set_refresh_tokens", methods=['POST'])
def set_refresh_tokens():
    global refresh_tokens
    refresh_tokens = request.get_json()
    return '', 204


@app.route(url_prefix + "/_remove_token/<token_id>", methods=['DELETE'])
def remove_token(token_id):
    try:
        del valid_tokens[token_id]
    except KeyError:
        return '', 404
    else:
        return '', 204


@app.route(url_prefix + "/_add_invalid_credentials", methods=['POST'])
def add_invalid_credentials():
    request_body = request.get_json()
    invalid_username_passwords.append((request_body['username'],
                                       request_body['password']))

    return '', 204


@app.route(url_prefix + "/_add_credentials_for_invalid_token", methods=['POST'])
def add_credentials_for_invalid_token():
    request_body = request.get_json()
    token_that_will_be_invalid_when_used.append((request_body['username'],
                                                 request_body['password']))

    return '', 204


@app.route(url_prefix + "/_add_valid_credentials", methods=['POST'])
def add_valid_credentials():
    request_body = request.get_json()
    valid_credentials[request_body['username']] = {
        'username': request_body['username'],
        'password': request_body['password'],
        'token': request_body['token'],
    }

    return '', 204


@app.route(url_prefix + "/0.1/token/<token>", methods=['HEAD'])
def token_head_ok(token):
    required_tenant_uuid = request.args.get('tenant')
    if required_tenant_uuid:
        token_tenant_uuid = valid_tokens[token]['metadata']['tenant_uuid']
        token_tenant = _find_tenant(token_tenant_uuid)
        visible_tenant_uuids = [tenant['uuid'] for tenant in _find_tenant_children(token_tenant)] + [token_tenant['uuid']]
        logger.debug('Visible tenants: %s', visible_tenant_uuids)
        if required_tenant_uuid not in visible_tenant_uuids:
            return '', 403

    required_acl = request.args.get('scope')
    if token in wrong_acl_tokens:
        if not required_acl:
            return '', 204
        return '', 403
    elif token in valid_tokens:
        if _valid_acl(token):
            return '', 204
        return '', 403
    else:
        return '', 404


@app.route(url_prefix + "/0.1/token/<token>", methods=['GET'])
def token_get(token):
    if token not in valid_tokens:
        return '', 404

    if not _valid_acl(token):
        return '', 403

    result = dict(valid_tokens[token])
    result['metadata'].setdefault('pbx_user_uuid', result['metadata']['uuid'])
    result.setdefault('auth_id', result['metadata']['uuid'])
    return jsonify({
        'data': result
    })


def _valid_acl(token_id):
    required_acl = request.args.get('scope')
    if required_acl and 'acl' in valid_tokens[token_id]:
        if required_acl in valid_tokens[token_id]['acl']:
            return True
        else:
            return False
    return True


@app.route(url_prefix + "/0.1/token", methods=['POST'])
def token_post():
    auth = request.authorization['username'], request.authorization['password']
    if auth in invalid_username_passwords:
        return '', 401
    elif auth in token_that_will_be_invalid_when_used:
        return jsonify({'data': {'auth_id': valid_tokens['valid-token']['auth_id'],
                                 'token': 'expired'}})
    elif request.authorization['username'] in valid_credentials:
        username = request.authorization['username']
        password = request.authorization['password']
        if password == valid_credentials[username]['password']:
            token = valid_credentials[username]['token']
            if token in valid_tokens:
                return jsonify({'data': valid_tokens[token]})
        return '', 401
    else:
        return jsonify({'data': valid_tokens['valid-token-multitenant']})


@app.route(url_prefix + "/0.1/tokens", methods=['GET'])
def tokens_get():
    result = {
        'items': refresh_tokens,
        'total': len(refresh_tokens),
        'filtered': len(refresh_tokens),
    }
    return jsonify(result), 200


@app.route(url_prefix + "/0.1/users", methods=['GET'])
def users_list():
    return jsonify({'items': [user for user in users.values()]})


@app.route(url_prefix + "/0.1/tenants", methods=['POST'])
def tenants_post():
    return jsonify(request.get_json())


@app.route(url_prefix + "/0.1/users", methods=['POST'])
def users_post():
    args = request.get_json()
    email = {'address': args['email_address']} if args.get('email_address') else None
    user = {
        'uuid': args.get('uuid', uuid.uuid4()),
        'firstname': args.get('firstname', None),
        'lastname': args.get('lastname', None),
        'username': args.get('username', None),
        'emails': [email] if email else [],
        'enabled': args.get('enabled', True),
        'tenant_uuid': request.headers.get('Wazo-Tenant', None)
    }
    users[user['uuid']] = user
    return jsonify(user)


@app.route(url_prefix + "/0.1/users/<user_uuid>", methods=['GET'])
def users_get(user_uuid):
    user = users.get(user_uuid)
    if not user:
        return '', 404
    return jsonify(user)


@app.route(url_prefix + "/0.1/users/<user_uuid>", methods=['PUT'])
def users_put(user_uuid):
    user = users.get(user_uuid)
    if not user:
        return '', 404
    args = request.get_json()
    args['uuid'] = user['uuid']
    args['emails'] = user['emails']
    args['enabled'] = args.get('enabled', True)
    users[args['uuid']] = args
    return jsonify(args)


@app.route(url_prefix + "/0.1/sessions", methods=['GET'])
def sessions_get():
    result = {
        'items': sessions,
        'total': len(sessions),
        'filtered': len(sessions),
    }
    return jsonify(result), 200


@app.route(url_prefix + "/0.1/tenants", methods=['GET'])
def tenants_get():
    token_uuid = request.headers['X-Auth-Token']
    token_tenant_uuid = valid_tokens[token_uuid]['metadata']['tenant_uuid']

    token_tenant = _find_tenant(token_tenant_uuid)
    if not token_tenant:
        return 'Tenant not found: {}'.format(token_tenant_uuid), 500

    token_tenant_children = _find_tenant_children(token_tenant)

    specified_tenant_uuid = request.headers.get('Wazo-Tenant')
    if specified_tenant_uuid:
        specified_tenant = _find_tenant(specified_tenant_uuid)
        if not specified_tenant:
            return 'Tenant not found: {}'.format(specified_tenant_uuid), 401

        specified_tenant_children = _find_tenant_children(specified_tenant)

        if specified_tenant not in [token_tenant] + token_tenant_children:
            return 'Unauthorized token', 401
    else:
        specified_tenant = token_tenant
        specified_tenant_children = token_tenant_children

    tenants_found = [specified_tenant] + specified_tenant_children

    tenants_filtered = _filter_tenants(tenants_found, **request.args.to_dict())

    result = {
        'items': tenants_filtered,
        'filtered': len(tenants_filtered),
        'total': len(tenants_found),
    }
    return jsonify(result), 200


def _find_tenant(tenant_uuid):
    for tenant in tenants:
        if tenant_uuid == tenant['uuid']:
            return tenant


def _find_tenant_children(search_tenant):
    result = []
    for tenant in tenants:
        if tenant['uuid'] == search_tenant['uuid']:
            continue
        if tenant['parent_uuid'] == search_tenant['uuid']:
            result.append(tenant)
            result = result + _find_tenant_children(tenant)
    return result


def _filter_tenants(tenants, name=None, **kwargs):
    if not name:
        return tenants

    result = [tenant for tenant in tenants if tenant['name'] == name]
    return result


@app.route(url_prefix + "/0.1/tenants/<tenant_uuid>", methods=['GET'])
def tenant_get(tenant_uuid):
    # Simulate master tenant by default
    parent_uuid = tenant_uuid
    for tenant in tenants:
        if tenant["uuid"] == tenant_uuid:
            parent_uuid = tenant["parent_uuid"]
            break
    return jsonify({'uuid': tenant_uuid, 'parent_uuid': parent_uuid}), 200


@app.route(url_prefix + "/0.1/users/<user_uuid>", methods=['DELETE'])
def users_delete(user_uuid):
    del users[user_uuid]
    return '', 204


@app.route(url_prefix + "/0.1/users/password/reset", methods=['POST'])
def users_password_reset():
    user_uuid = request.args.get('user_uuid')
    user = users.get(user_uuid)
    if not user:
        return '', 404
    return '', 204


@app.route(url_prefix + "/0.1/admin/users/<user_uuid>/emails", methods=['PUT'])
def admin_users_emails_put(user_uuid):
    user = users.get(user_uuid)
    if not user:
        return '', 404
    emails = request.get_json()['emails']
    users[user['uuid']]['emails'] = emails
    return jsonify(emails)


@app.route(url_prefix + "/0.1/policies", methods=['GET'])
def policies_get():
    policies_dict = dict(DEFAULT_POLICIES)
    name = request.args.get('name')
    policies = [policies_dict.get(name)] if name else policies_dict.items()

    return jsonify({
        'items': policies,
        'total': len(policies),
        'filtered': len(policies),
    }), 200


@app.route(url_prefix + "/0.1/users/<user_uuid>/policies/<policy_uuid>", methods=['PUT'])
def users_policies_put(user_uuid, policy_uuid):
    return '', 204


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=port, debug=True)
