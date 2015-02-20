#!/usr/bin/env python
'''
status

Blueprint definition for the status application

'''
from flask import Blueprint

api = Blueprint('status', __name__)

# Exposed Endpoints
from status.controller import test

from status.tasks import get_dac_status
