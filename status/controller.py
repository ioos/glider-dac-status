#!/usr/bin/env python
'''
status.controller

The controller definition for the status application. This mostly contains the
routes and logic API
'''

from status import api
from status.tasks import get_dac_status, STATUS_OK, STATUS_FAIL

from flask import jsonify, request

@api.route('/test')
def test():
    return jsonify(message="Running")

