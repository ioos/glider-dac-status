#!/usr/bin/env python
'''
navo.controller

Controller definitions for the NAVO Glider View(s)
'''
from navo import api
from flask import jsonify, render_template
from glob import glob
import json
import pkg_resources
import navo
import os

@api.route('/')
def index():
    assets_json = pkg_resources.resource_string(__name__, 'assets.json')
    assets = json.loads(assets_json)

    js_key = "static/build/js/main.min.js"
    js_files = []
    for filepath in assets['main']['js'][js_key]:
        if '*' not in filepath:
            js_files.append(filepath)
        else:
            filepath = os.path.join('navo', filepath)
            for glob_path in glob(filepath):
                glob_path = glob_path.split('navo/')[1]
                js_files.append(glob_path)
    css_files = []
    css_key = "static/build/css/main.min.css"
    for filepath in assets['main']['css'][css_key]:
        if '*' not in filepath:
            css_files.append(filepath)
        else:
            filepath = os.path.join('navo', filepath)
            for glob_path in glob(filepath):
                glob_path = glob_path.split('navo/')[1]
                css_files.append(glob_path)

    js_template_strings = ['<script type="text/javascript" src="%s"></script>' % i for i in js_files]
    css_template_strings = ['<link rel="stylesheet" type="text/css" href="%s" />' % i for i in css_files]
    return render_template('index.html', css='\n'.join(css_template_strings), javascripts='\n'.join(js_template_strings))

