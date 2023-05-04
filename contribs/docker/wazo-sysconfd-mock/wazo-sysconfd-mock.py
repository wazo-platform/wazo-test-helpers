#!/usr/bin/python3
# Copyright 2018-2023 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later
from __future__ import annotations

import logging
import sys

from collections import deque
from flask import Flask, request, jsonify, Response

app = Flask(__name__)
port = sys.argv[1]
logger = logging.getLogger('wazo-sysconfd-mock')

_requests = deque(maxlen=1024)


@app.errorhandler(500)
def handle_generic(e: Exception) -> Response:
    logger.error(f'Exception: {e}')
    return jsonify({'error': str(e)})


@app.before_request
def log_request() -> None:
    if not request.path.startswith('/_requests'):
        path = request.path
        log = {'method': request.method,
               'path': path,
               'query': dict(request.args.items(multi=True)),
               'body': request.data.decode('utf-8'),
               'json': request.json if request.is_json else None,
               'headers': dict(request.headers)}
        _requests.append(log)


@app.route('/_requests', methods=['GET'])
def list_requests() -> Response:
    return jsonify(requests=list(_requests))


@app.route('/_requests', methods=['DELETE'])
def delete_requests() -> str:
    _requests.clear()
    return ''


@app.route('/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE'])
def fallback(path: str) -> str:
    return ''


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=port)
