#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright 2015-2018 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0+

import uuid
import sys

from flask import Flask, jsonify, request

app = Flask(__name__)

port = int(sys.argv[1])

context = ('/usr/local/share/ssl/auth/server.crt', '/usr/local/share/ssl/auth/server.key')

valid_tokens = {'valid-token': {'auth_id': 'uuid', 'token': 'valid-token'}}
wrong_acl_tokens = {'invalid-acl-token'}
invalid_username_passwords = [('test', 'foobar')]
token_that_will_be_invalid_when_used = [('test', 'iddqd')]
users = {}


@app.route("/_set_token", methods=['POST'])
def add_token():
    request_body = request.get_json()
    token = request_body['token']

    valid_tokens[token] = request_body

    return '', 204


@app.route("/_remove_token/<token_id>", methods=['DELETE'])
def set_token(token_id):
    try:
        del valid_tokens[token_id]
    except KeyError:
        return '', 404
    else:
        return '', 204


@app.route("/0.1/token/<token>", methods=['HEAD'])
def token_head_ok(token):
    if token in wrong_acl_tokens:
        return '', 403
    elif token in valid_tokens:
        if _valid_acl(token):
            return '', 204
        return '', 403
    else:
        return '', 401


@app.route("/0.1/token/<token>", methods=['GET'])
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


@app.route("/0.1/token", methods=['POST'])
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


@app.route("/0.1/users", methods=['GET'])
def users_list():
    return jsonify({'items': [user for user in users.values()]})


@app.route("/0.1/users", methods=['POST'])
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


@app.route("/0.1/users/<user_uuid>", methods=['GET'])
def users_get(user_uuid):
    user = users.get(user_uuid)
    if not user:
        return '', 404
    return jsonify(user)


@app.route("/0.1/users/<user_uuid>", methods=['PUT'])
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


@app.route("/0.1/users/<user_uuid>", methods=['DELETE'])
def users_delete(user_uuid):
    del users[user_uuid]
    return '', 204


@app.route("/0.1/users/password/reset", methods=['POST'])
def users_password_reset():
    user_uuid = request.args.get('user_uuid')
    user = users.get(user_uuid)
    if not user:
        return '', 404
    return '', 204


@app.route("/0.1/admin/users/<user_uuid>/emails", methods=['PUT'])
def admin_users_emails_put(user_uuid):
    user = users.get(user_uuid)
    if not user:
        return '', 404
    emails = request.get_json()['emails']
    users[user['uuid']]['emails'] = emails
    return jsonify(emails)


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=port, ssl_context=context, debug=True)
