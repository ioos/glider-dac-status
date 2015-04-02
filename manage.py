from flask.ext.script import Manager
from app import app
from flask import url_for


manager = Manager(app)

@manager.command
def get_status():
    from status.tasks import get_dac_status
    result = get_dac_status.delay()
    result.wait()

@manager.command
def get_trajectory_features():
    from status.tasks import get_trajectory_features
    result = get_trajectory_features.delay()
    result.wait()

@manager.command
def get_email():
    from navo.email_extractor import process
    with app.app_context():
        process()

@manager.command
def update_trajectory_cache():
    from navo.tasks import update_cache
    with app.app_context():
        update_cache()

@manager.command
def list_routes():
    import urllib
    output = []
    for rule in app.url_map.iter_rules():

        options = {}
        for arg in rule.arguments:
            options[arg] = "[{0}]".format(arg)

        methods = ','.join(rule.methods)
        url = url_for(rule.endpoint, **options)
        line = urllib.unquote("{:50s} {:20s} {}".format(rule.endpoint, methods, url))
        output.append(line)

    for line in sorted(output):
        print line

if __name__ == '__main__':
    manager.run()
