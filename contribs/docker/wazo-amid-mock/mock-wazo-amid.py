#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright 2019-2020 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

import json
import logging
import sys

from flask import Flask
from flask import jsonify
from flask import request

logging.basicConfig(level=logging.DEBUG)


app = Flask(__name__)
logger = logging.getLogger('amid-mock')

_requests = []
_responses = {'action': {'DeviceStateList': [], 'CoreShowChannels': []}}


def _reset():
    global _requests
    global _responses
    _requests = []
    _responses = {'action': {'DeviceStateList': [], 'CoreShowChannels': []}}


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


@app.route('/_requests', methods=['GET'])
def list_requests():
    return jsonify(requests=_requests)


@app.route('/_reset', methods=['POST'])
def reset():
    _reset()
    return '', 204


@app.route('/_set_response', methods=['POST'])
def set_response():
    global _responses
    request_body = json.loads(request.data)
    set_response = request_body['response']
    set_response_body = request_body['content']
    _responses[set_response] = set_response_body
    return '', 204


@app.route('/_set_response_action', methods=['POST'])
def set_response_action():
    global _responses
    request_body = json.loads(request.data)
    set_response = request_body['response']
    set_response_body = request_body['content']
    _responses['action'][set_response] = set_response_body
    return '', 204


@app.route('/1.0/action/<action>', methods=['POST'])
def action(action):
    return jsonify(_responses['action'][action])


if __name__ == '__main__':
    _reset()

    port = int(sys.argv[1])
    app.run(host='0.0.0.0', port=port, debug=True)
