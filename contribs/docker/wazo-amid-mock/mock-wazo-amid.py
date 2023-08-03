#!/usr/bin/env python3
# Copyright 2019-2023 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later
from __future__ import annotations

import json
import logging
import sys

from collections import deque
from flask import Flask, jsonify, request, Response

logging.basicConfig(level=logging.DEBUG)


app = Flask(__name__)
logger = logging.getLogger('amid-mock')

EMPTY_RESPONSES = {
    'action': {
        'DeviceStateList': [],
        'CoreShowChannels': [],
        'Command': {'response': ['Success']},
    }
}

_requests: deque[dict] = deque(maxlen=1024)
_responses: dict[str, dict] = dict(EMPTY_RESPONSES)


def _reset() -> None:
    _requests.clear()

    global _responses
    _responses = dict(EMPTY_RESPONSES)


@app.errorhandler(500)
def handle_generic(e: Exception) -> Response:
    logger.error(f'Exception: {e}')
    return jsonify({'error': str(e)})


@app.before_request
def log_request() -> None:
    if not request.path.startswith('/_'):
        path = request.path
        log = {
            'method': request.method,
            'path': path,
            'query': dict(request.args.items(multi=True)),
            'body': request.data.decode('utf-8'),
            'json': request.json if request.is_json else None,
            'headers': dict(request.headers),
        }
        _requests.append(log)


@app.after_request
def print_request_response(response: Response) -> Response:
    logger.debug(
        'request: %s',
        {
            'method': request.method,
            'path': request.path,
            'query': dict(request.args.items(multi=True)),
            'body': request.data.decode('utf-8'),
            'headers': dict(request.headers),
        },
    )
    logger.debug(
        'response: %s',
        {
            'body': response.data.decode('utf-8'),
        },
    )
    return response


@app.route('/_requests', methods=['GET'])
def list_requests() -> Response:
    return jsonify(requests=list(_requests))


@app.route('/_reset', methods=['POST'])
def reset() -> tuple[str, int]:
    _reset()
    return '', 204


@app.route('/_set_response', methods=['POST'])
def set_response() -> tuple[str, int]:
    global _responses
    request_body = json.loads(request.data)
    set_response = request_body['response']
    set_response_body = request_body['content']
    _responses[set_response] = set_response_body
    return '', 204


@app.route('/_set_response_action', methods=['POST'])
def set_response_action() -> tuple[str, int]:
    global _responses
    request_body = json.loads(request.data)
    set_response = request_body['response']
    set_response_body = request_body['content']
    _responses['action'][set_response] = set_response_body
    return '', 204


@app.route('/1.0/action/<action>', methods=['POST'])
def action(action: str) -> Response:
    return jsonify(_responses['action'][action])


if __name__ == '__main__':
    _reset()

    port = int(sys.argv[1])
    app.run(host='0.0.0.0', port=port, debug=True)
