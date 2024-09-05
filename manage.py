from flask_script import Manager
from app import app
from flask import url_for


manager = Manager(app)

@manager.command
def get_status():
    from status.tasks import get_dac_status
    result = get_dac_status.delay()

@manager.command
def get_trajectory_features():
    from status.tasks import get_trajectory_features
    result = get_trajectory_features.delay()

@manager.command
def list_routes():
    import urllib.request, urllib.parse, urllib.error
    output = []
    for rule in app.url_map.iter_rules():

        options = {}
        for arg in rule.arguments:
            options[arg] = "[{0}]".format(arg)

        methods = ','.join(rule.methods)
        url = url_for(rule.endpoint, **options)
        line = urllib.parse.unquote("{:50s} {:20s} {}".format(rule.endpoint, methods, url))
        output.append(line)

if __name__ == '__main__':
    manager.run()
