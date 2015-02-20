#!/usr/bin/env python
'''
web.controller

The controller for the web stuff
'''

from web import api

@api.route('/')
def index():
    return api.send_static_file('index.html')
