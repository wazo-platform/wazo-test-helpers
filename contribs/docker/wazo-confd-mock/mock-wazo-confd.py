#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright 2015-2021 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

import json
import logging
import sys

from flask import Flask
from flask import jsonify
from flask import request

logging.basicConfig(level=logging.DEBUG)

_EMPTY_RESPONSES = {
    'applications': {},
    'asterisk/rtp/general': {},
    'conferences': {},
    'contexts': {},
    'infos': {},
    'lines': {},
    'meetings': {},
    'moh': {
        '60f123e6-147b-487c-b08a-36395d43346e': {
            'uuid': '60f123e6-147b-487c-b08a-36395d43346e',
            'name': 'default',
        },
    },
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

_requests = []
_responses = {}


def _reset():
    global _requests
    global _responses
    _requests = []
    _responses = dict(_EMPTY_RESPONSES)


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


@app.route('/1.1/asterisk/rtp/general')
def asterisk_rtp_general():
    return jsonify(_responses['asterisk/rtp/general'])


@app.route('/1.1/asterisk/rtp/general', methods=['PUT'])
def asterisk_rtp_general_put():
    return '', 204


@app.route('/1.1/applications')
def applications():
    return jsonify({'items': _responses['applications'].values()})


@app.route('/1.1/applications/<application_uuid>')
def application(application_uuid):
    if application_uuid not in _responses['applications']:
        return '', 404
    return jsonify(_responses['applications'][application_uuid])


@app.route('/1.1/conferences')
def conferences():
    conferences = _responses['conferences'].values()
    if 'name' in request.args:
        conferences = [conference for conference in conferences if conference['name'] == request.args['name']]
    return jsonify({'items': conferences})


@app.route('/1.1/conferences/<conference_id>')
def conference(conference_id):
    if conference_id not in _responses['conferences']:
        return '', 404
    return jsonify(_responses['conferences'][conference_id])


@app.route('/1.1/infos')
def infos():
    return jsonify(_responses['infos'])


@app.route('/1.1/lines')
def lines():
    lines = _responses['lines'].values()
    if 'name' in request.args:
        lines = [line for line in lines if line['name'] == request.args['name']]
    return jsonify({'items': lines})


@app.route('/1.1/lines/<line_id>')
def line(line_id):
    if line_id not in _responses['lines']:
        return '', 404
    return jsonify(_responses['lines'][line_id])


@app.route('/1.1/moh')
def moh():
    recurse = request.args.get('recurse')
    items = _responses['moh'].values() if recurse else []
    return jsonify({'items': items})


@app.route('/1.1/contexts')
def contexts():
    return jsonify({'items': _responses['contexts'].values()})


@app.route('/1.1/contexts/<context_id>')
def context(context_id):
    if context_id not in _responses['contexts']:
        return '', 404
    return jsonify(_responses['contexts'][context_id])


@app.route('/1.1/meetings')
def meetings():
    meetings = _responses['meetings'].values()
    if 'name' in request.args:
        meetings = [meeting for meeting in meetings if meeting['name'] == request.args['name']]
    return jsonify({'items': meetings})


@app.route('/1.1/meetings/<meeting_uuid>')
def meeting(meeting_uuid):
    if meeting_uuid not in _responses['meetings']:
        return '', 404
    return jsonify(_responses['meetings'][meeting_uuid])


@app.route('/1.1/switchboards')
def switchboards():
    return jsonify({'items': _responses['switchboards'].values()})


@app.route('/1.1/switchboards/<switchboard_uuid>')
def switchboard(switchboard_uuid):
    if switchboard_uuid not in _responses['switchboards']:
        return '', 404
    return jsonify(_responses['switchboards'][switchboard_uuid])


@app.route('/1.1/users')
def users():
    return jsonify({'items': _responses['users'].values()})


@app.route('/1.1/users/<user_uuid>')
def user(user_uuid):
    if user_uuid not in _responses['users']:
        return '', 404
    return jsonify(_responses['users'][user_uuid])


@app.route('/1.1/users/<user_uuid>/lines')
def lines_of_user(user_uuid):
    if user_uuid not in _responses['users']:
        return '', 404

    return jsonify({
        'items': _responses['user_lines'].get(user_uuid, [])
    })


@app.route('/1.1/users/<user_uuid>/voicemails')
def voicemails_of_user(user_uuid):
    return jsonify({
        'items': _responses['user_voicemails'].get(user_uuid, [])
    })


@app.route('/1.1/trunks')
def trunks():
    items = _responses['trunks'].values()
    total = len(items)
    return jsonify({'items': items, 'total': total})


@app.route('/1.1/trunks/<trunk_id>')
def trunk(trunk_id):
    return jsonify(_responses['trunks'][trunk_id])


@app.route('/1.1/voicemails')
def voicemails():
    return jsonify({'items': _responses['voicemails'].values()})


@app.route('/1.1/voicemails/<voicemail_id>')
def voicemail(voicemail_id):
    return jsonify(_responses['voicemails'][voicemail_id])


@app.route('/1.1/wizard')
def wizard_get():
    return jsonify(_responses['wizard'])


@app.route('/1.1/wizard', methods=['POST'])
def wizard_post():
    if _responses['wizard'].get('fail'):
        raise RuntimeError('Raising expected failure')
    return jsonify(_responses['wizard'])


@app.route('/1.1/wizard/discover')
def wizard_discover():
    return jsonify(_responses['wizard_discover'])


if __name__ == '__main__':
    _reset()

    port = int(sys.argv[1])
    app.run(host='0.0.0.0', port=port, debug=True)
