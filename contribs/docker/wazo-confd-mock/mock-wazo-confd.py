#!/usr/bin/env python3
# Copyright 2015-2024 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later
from __future__ import annotations

import json
import logging
import sys
from collections import deque
from typing import Any

from flask import Flask, Response, jsonify, request

logging.basicConfig(level=logging.DEBUG)

_EMPTY_RESPONSES = {
    'applications': {},
    'asterisk/rtp/general': {},
    'conferences': {},
    'contexts': {},
    'infos': {},
    'ingresses': {},
    'lines': {},
    'meetings': {},
    'moh': {
        '60f123e6-147b-487c-b08a-36395d43346e': {
            'uuid': '60f123e6-147b-487c-b08a-36395d43346e',
            'name': 'default',
        },
    },
    'parkinglots': {},
    'switchboards': {},
    'trunks': {},
    'user_lines': {},
    'user_voicemails': {},
    'users': {},
    'voicemails': {},
    'wizard_discover': {},
    'wizard': {},
}

app = Flask(__name__)
logger = logging.getLogger('confd-mock')

_requests: deque[dict] = deque(maxlen=1024)
_responses: dict[str, Any] = dict(_EMPTY_RESPONSES)


def _reset() -> None:
    _requests.clear()

    global _responses
    _responses = dict(_EMPTY_RESPONSES)


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


@app.route('/1.1/asterisk/rtp/general')
def asterisk_rtp_general() -> Response:
    return jsonify(_responses['asterisk/rtp/general'])


@app.route('/1.1/asterisk/rtp/general', methods=['PUT'])
def asterisk_rtp_general_put() -> tuple[str, int]:
    return '', 204


@app.route('/1.1/applications')
def applications() -> Response:
    return jsonify({'items': list(_responses['applications'].values())})


@app.route('/1.1/applications/<application_uuid>')
def application(application_uuid: str) -> Response | tuple[str, int]:
    if application_uuid not in _responses['applications']:
        return '', 404
    return jsonify(_responses['applications'][application_uuid])


@app.route('/1.1/conferences')
def conferences() -> Response:
    conferences = list(_responses['conferences'].values())
    if 'name' in request.args:
        conferences = [
            conference
            for conference in conferences
            if conference['name'] == request.args['name']
        ]
    return jsonify({'items': conferences})


@app.route('/1.1/conferences/<conference_id>')
def conference(conference_id: str) -> Response | tuple[str, int]:
    if conference_id not in _responses['conferences']:
        return '', 404
    return jsonify(_responses['conferences'][conference_id])


@app.route('/1.1/infos')
def infos() -> Response:
    return jsonify(_responses['infos'])


@app.route('/1.1/ingresses/http')
def ingresses() -> Response:
    return jsonify({'items': list(_responses['ingresses'].values())})


@app.route('/1.1/lines')
def lines() -> Response:
    lines = list(_responses['lines'].values())
    if 'name' in request.args:
        lines = [line for line in lines if line['name'] == request.args['name']]
    return jsonify({'items': lines})


@app.route('/1.1/lines/<line_id>')
def line(line_id: str) -> Response | tuple[str, int]:
    if line_id not in _responses['lines']:
        return '', 404
    return jsonify(_responses['lines'][line_id])


@app.route('/1.1/moh')
def moh() -> Response:
    recurse = request.args.get('recurse')
    items = list(_responses['moh'].values()) if recurse else []
    return jsonify({'items': items})


@app.route('/1.1/contexts')
def contexts() -> Response:
    return jsonify({'items': list(_responses['contexts'].values())})


@app.route('/1.1/contexts/<context_id>')
def context(context_id: str) -> Response | tuple[str, int]:
    if context_id not in _responses['contexts']:
        return '', 404
    return jsonify(_responses['contexts'][context_id])


@app.route('/1.1/meetings')
def meetings() -> Response:
    meetings = list(_responses['meetings'].values())
    if 'name' in request.args:
        meetings = [
            meeting for meeting in meetings if meeting['name'] == request.args['name']
        ]
    return jsonify({'items': meetings})


@app.route('/1.1/meetings/<meeting_uuid>')
def meeting(meeting_uuid: str) -> Response | tuple[str, int]:
    if meeting_uuid not in _responses['meetings']:
        return '', 404
    return jsonify(_responses['meetings'][meeting_uuid])


@app.route('/1.1/parkinglots')
def parkinglots() -> Response:
    return jsonify({'items': list(_responses['parkinglots'].values())})


@app.route('/1.1/parkinglots/<parking_id>')
def parkinglot(parking_id: int) -> Response | tuple[str, int]:
    if parking_id not in _responses['parkinglots']:
        return '', 404
    return jsonify(_responses['parkinglots'][parking_id])


@app.route('/1.1/switchboards')
def switchboards() -> Response:
    return jsonify({'items': list(_responses['switchboards'].values())})


@app.route('/1.1/switchboards/<switchboard_uuid>')
def switchboard(switchboard_uuid: str) -> Response | tuple[str, int]:
    if switchboard_uuid not in _responses['switchboards']:
        return '', 404
    return jsonify(_responses['switchboards'][switchboard_uuid])


@app.route('/1.1/users')
def users() -> Response:
    users = list(_responses['users'].values())

    tenant_uuid = request.headers.get('Wazo-Tenant')
    if tenant_uuid:
        users = [user for user in users if user['tenant_uuid'] == tenant_uuid]

    return jsonify({'items': users, 'total': len(users)})


@app.route('/1.1/users/<user_uuid>')
def user(user_uuid: str) -> Response | tuple[str, int]:
    if user_uuid not in _responses['users']:
        return '', 404

    user = _responses['users'][user_uuid]

    tenant_uuid = request.headers.get('Wazo-Tenant')
    if tenant_uuid and tenant_uuid != user['tenant_uuid']:
        return '', 404

    return jsonify(user)


@app.route('/1.1/users/<user_uuid>/lines')
def lines_of_user(user_uuid: str) -> Response | tuple[str, int]:
    if user_uuid not in _responses['users']:
        return '', 404

    user = _responses['users'][user_uuid]
    tenant_uuid = request.headers.get('Wazo-Tenant')
    if tenant_uuid and tenant_uuid != user['tenant_uuid']:
        return '', 404

    return jsonify({'items': _responses['user_lines'].get(user_uuid, [])})


@app.route('/1.1/users/<user_uuid>/voicemails')
def voicemails_of_user(user_uuid: str) -> Response:
    return jsonify({'items': _responses['user_voicemails'].get(user_uuid, [])})


@app.route('/1.1/trunks')
def trunks() -> Response:
    items = list(_responses['trunks'].values())
    total = len(items)
    return jsonify({'items': items, 'total': total})


@app.route('/1.1/trunks/<trunk_id>')
def trunk(trunk_id: str) -> Response:
    return jsonify(_responses['trunks'][trunk_id])


@app.route('/1.1/voicemails')
def voicemails() -> Response:
    return jsonify({'items': list(_responses['voicemails'].values())})


@app.route('/1.1/voicemails/<voicemail_id>')
def voicemail(voicemail_id: str) -> Response:
    return jsonify(_responses['voicemails'][voicemail_id])


@app.route('/1.1/wizard')
def wizard_get() -> Response:
    return jsonify(_responses['wizard'])


@app.route('/1.1/wizard', methods=['POST'])
def wizard_post() -> Response:
    if _responses['wizard'].get('fail'):
        raise RuntimeError('Raising expected failure')
    return jsonify(_responses['wizard'])


@app.route('/1.1/wizard/discover')
def wizard_discover() -> Response:
    return jsonify(_responses['wizard_discover'])


if __name__ == '__main__':
    _reset()

    port = int(sys.argv[1])
    app.run(host='0.0.0.0', port=port, debug=True)
