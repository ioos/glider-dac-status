#!/usr/bin/env python
'''
web.controller

The controller for the web stuff
'''

from web import api
from flask import render_template, url_for

@api.route('/')
def index():
    return api.send_static_file('index.html')

@api.route('/summary')
@api.route('/summary/')
def summary():
    return render_template('summary.html')
