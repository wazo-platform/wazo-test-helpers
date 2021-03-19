#!/usr/bin/python2
# Copyright 2018 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

import sys

from flask import Flask, request, jsonify

app = Flask(__name__)
port = sys.argv[1]

REQUESTS = []


@app.before_request
def log_request():
    if not request.path.startswith('/_requests'):
        path = request.path
        log = {'method': request.method,
               'path': path,
               'query': dict(request.args.items()),
               'body': request.data,
               'json': request.json,
               'headers': dict(request.headers)}
        REQUESTS.append(log)


@app.route('/_requests', methods=['GET'])
def list_requests():
    return jsonify(requests=REQUESTS)


@app.route('/_requests', methods=['DELETE'])
def delete_requests():
    global REQUESTS
    REQUESTS = []
    return ''


@app.route('/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE'])
def fallback(path):
    return ''


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=port)
