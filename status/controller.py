#!/usr/bin/env python
'''
status.controller

The controller definition for the status application. This mostly contains the
routes and logic API
'''

from status import api

from flask import jsonify

@api.route('/test')
def test():
    return jsonify(message='test')

