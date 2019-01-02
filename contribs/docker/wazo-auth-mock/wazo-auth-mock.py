#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright 2015-2019 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0+

import logging
import uuid
import sys

from flask import Flask, jsonify, request

logger = logging.getLogger()

app = Flask(__name__)

port = int(sys.argv[1])
try:
    url_prefix = sys.argv[2]
except IndexError:
    url_prefix = ''

context = ('/usr/local/share/ssl/auth/server.crt', '/usr/local/share/ssl/auth/server.key')

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
        'xivo_user_uuid': 'uuid',
        'metadata': {
            'uuid': 'uuid',
            'tenant_uuid': 'ffffffff-ffff-ffff-ffff-ffffffffffff',
            'tenants': [
                {
                    'uuid': 'ffffffff-ffff-ffff-ffff-ffffffffffff',
                    'name': 'valid-tenant',
                }
            ]
        }
    },
    'valid-token-multitenant': {
        'auth_id': 'uuid-multitenant',
        'token': 'valid-token-multitenant',
        'xivo_user_uuid': 'uuid-multitenant',
        'metadata': {
            'uuid': 'uuid-multitenant',
            'tenant_uuid': 'eeeeeeee-eeee-eeee-eeee-eeeeeeeeeee1',
            'tenants': [
                {
                    'uuid': 'eeeeeeee-eeee-eeee-eeee-eeeeeeeeeee1',
                    'name': 'valid-tenant1',
                },
                {
                    'uuid': 'eeeeeeee-eeee-eeee-eeee-eeeeeeeeeee2',
                    'name': 'valid-tenant2',
                },
                {
                    'uuid': 'eeeeeeee-eeee-eeee-eeee-eeeeeeeeeee3',
                    'name': 'valid-tenant3',
                },
            ]
        }
    },
    'valid-token-master-tenant': {
        'auth_id': 'uuid-tenant-master',
        'token': 'valid-token-master-tenant',
        'xivo_user_uuid': 'uuid-tenant-master',
        'metadata': {
            'uuid': 'uuid-tenant-master',
            'tenant_uuid': 'eeeeeeee-eeee-eeee-eeee-eeeeeeeeee10',
            'tenants': [
                {
                    'uuid': 'eeeeeeee-eeee-eeee-eeee-eeeeeeeeee10',
                    'name': 'master-tenant',
                },
                {
                    'uuid': 'eeeeeeee-eeee-eeee-eeee-eeeeeeeeee11',
                    'name': 'sub-tenant',
                },
            ]
        }
    },
    'valid-token-sub-tenant': {
        'auth_id': 'uuid-subtenant',
        'token': 'valid-token-sub-tenant',
        'xivo_user_uuid': 'uuid-subtenant',
        'metadata': {
            'uuid': 'uuid-subtenant',
            'tenant_uuid': 'eeeeeeee-eeee-eeee-eeee-eeeeeeeeee11',
            'tenants': [
                {
                    'uuid': 'eeeeeeee-eeee-eeee-eeee-eeeeeeeeee11',
                    'name': 'sub-tenant',
                },
            ]
        }
    },
    'non-user-token': {
        'auth_id': 'uuid-non-user',
        'token': 'non-user-token',
        'xivo_user_uuid': None,
        'metadata': {
            'uuid': None,
            'tenant_uuid': 'dddddddd-dddd-dddd-dddd-dddddddddd11',
        }
    }
}
wrong_acl_tokens = {'invalid-acl-token'}
invalid_username_passwords = [('test', 'foobar')]
token_that_will_be_invalid_when_used = [('test', 'iddqd')]
users = {}

_requests = []


def _reset():
    global _requests
    _requests = []


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


@app.route(url_prefix + "/_set_token", methods=['POST'])
def set_token():
    request_body = request.get_json()
    token = request_body['token']

    valid_tokens[token] = request_body

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


@app.route(url_prefix + "/0.1/token/<token>", methods=['HEAD'])
def token_head_ok(token):
    if token in wrong_acl_tokens:
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
    result.setdefault('xivo_user_uuid', result['auth_id'])
    return jsonify({
        'data': result
    })


def _valid_acl(token_id):
    required_acl = request.args.get('scope')
    if required_acl and 'acls' in valid_tokens[token_id]:
        if required_acl in valid_tokens[token_id]['acls']:
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
    else:
        return jsonify({'data': {'auth_id': valid_tokens['valid-token']['auth_id'],
                                 'token': 'valid-token'}})


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
    }
    users[user['uuid']] = user
    return jsonify(user)


@app.route(url_prefix + "/0.1/users/<user_uuid>", methods=['GET'])
def users_get(user_uuid):
    user = users.get(user_uuid)
    if not user:
        return '', 404
    return jsonify(user)


@app.route(url_prefix + "/0.1/users/<user_uuid>/tenants", methods=['GET'])
def users_get_tenants(user_uuid):
    tenants = None

    for body in valid_tokens.itervalues():
        if body['metadata']['uuid'] != user_uuid:
            continue
        tenants = body['metadata']['tenants']

    if tenants is None:
        print 'did not find', user_uuid
        return '', 404

    result = {
        'total': len(tenants),
        'filtered': len(tenants),
        'items': tenants,
    }

    return jsonify(result), 200


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


@app.route(url_prefix + "/0.1/tenants", methods=['GET'])
def tenants_get():
    specified_tenant = request.headers['Wazo-Tenant']
    for key, value in valid_tokens.items():
        if valid_tokens[key]['metadata']['tenant_uuid'] == specified_tenant:
            tenants = valid_tokens[key]['metadata']['tenants']
            return jsonify({
                'items': tenants,
                'total': len(tenants),
                'filtered': len(tenants),
            }), 200
    return jsonify({
        'items': [{'uuid': specified_tenant}],
        'total': 1,
        'filtered': 1,
    }), 200


@app.route(url_prefix + "/0.1/tenants/<tenant_uuid>", methods=['GET'])
def tenant_get(tenant_uuid):
    # Simulate master tenant
    return jsonify({'uuid': tenant_uuid, 'parent_uuid': tenant_uuid}), 200


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
    app.run(host='0.0.0.0', port=port, ssl_context=context, debug=True)
