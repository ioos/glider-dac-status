#!/usr/bin/env python
'''
navo

Blueprint for the navo page
'''
from flask import Blueprint

api = Blueprint('navo', __name__, template_folder='templates', static_folder='static')

from navo.controller import *

