#!/usr/bin/env python
'''
app

The application context
'''
from celery import Celery
from celery.schedules import crontab
from flask import Flask, url_for, jsonify
from flask_environments import Environments
import os


celery = Celery('__main__')

app = Flask(__name__, static_folder='web/static')
env = Environments(app, default_env='DEVELOPMENT')
env.from_yaml('config.yml')
# Override config file with local version
if os.path.exists('config.local.yml'):
    env.from_yaml('config.local.yml')

celery.conf.update(broker_url=app.config['REDIS_URL'],
                   result_backend=app.config['REDIS_URL'])

TaskBase = celery.Task


class ContextTask(TaskBase):
    abstract = True

    def __call__(self, *args, **kwargs):
        with app.app_context():
            return TaskBase.__call__(self, *args, **kwargs)


celery.Task = ContextTask

# Set up periodic tasks
celery.conf.beat_schedule = {
    "get_dac_status_task": {
        "task": "status.tasks.get_dac_status",
        "schedule": crontab(minute="*/15")  # Run every 15 mins
    },
    "get_dac_profile_plots_task": {
        "task": "status.tasks.generate_dac_profile_plots",
        "schedule": crontab(minute=0, hour=[0, 12])  # Run twice a day
    },
}

if app.config['LOGGING'] is True:
    import logging
    logger = logging.getLogger('replicate')
    logger.setLevel(logging.DEBUG)

    log_directory = app.config.get('LOG_DIRECTORY', 'logs')
    log_filename = app.config.get('LOG_FILE', 'status.log')
    log_path = os.path.join(log_directory, log_filename)
    if not os.path.exists(log_directory):
        os.makedirs(log_directory)
    file_handler = logging.FileHandler(log_path, mode='a+')

    stream_handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(process)d - %(name)s - %(module)s:%(lineno)d - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    stream_handler.setFormatter(formatter)
    app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.DEBUG)
    app.logger.info('Application Process Started')


def has_no_empty_params(rule):
    '''
    Something to do with empty params?
    '''
    defaults = rule.defaults if rule.defaults is not None else ()
    arguments = rule.arguments if rule.arguments is not None else ()
    return len(defaults) >= len(arguments)


def site_map():
    '''
    Returns a json structure for the site routes and handlers
    '''
    links = []
    for rule in app.url_map.iter_rules():
        # Filter out rules we can't navigate to in a browser
        # and rules that require parameters
        if "GET" in rule.methods and has_no_empty_params(rule):
            url = url_for(rule.endpoint)
            links.append((url, rule.endpoint))
    # links is now a list of url, endpoint tuples
    return jsonify(rules=links)


# handle proxy server headers
from status.reverse_proxy import ReverseProxied
app.wsgi_app = ReverseProxied(app.wsgi_app)

from status import api as status_blueprint
app.register_blueprint(status_blueprint, url_prefix='/api')

from web import api as web_blueprint
app.register_blueprint(web_blueprint)

if app.config['DEBUG']:
    app.add_url_rule('/site-map', 'site_map', site_map)


def main():
    '''
    Runs the application
    '''
    app.run(host=app.config['HOST'], port=app.config['PORT'],
            debug=app.config['DEBUG'])
    return 0


if __name__ == '__main__':
    main()
