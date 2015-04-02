#!/usr/bin/env python
'''
web

The Web application. You know, templates and stuff.
'''

from flask import Blueprint

api = Blueprint('web', __name__, template_folder='templates', static_folder='static', static_url_path='/summary/static')

# Exposed Endpoints
from web.controller import index
