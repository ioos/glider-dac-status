#!/usr/bin/env python
'''
app

The application context
'''
from flask import Flask
from flask_environments import Environments
from status.reverse_proxy import ReverseProxied
import os


def create_app(config_name):
    '''
    Returns an instance of the application context
    '''
    app = Flask(__name__)
    env = Environments(app, default_env=config_name)
    env.from_yaml('config.yml')
    if app.config['LOGGING'] == True:
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
        #app.logger.addHandler(stream_handler)
        app.logger.setLevel(logging.DEBUG)
        app.logger.info('Application Process Started')

    # handle proxy server headers
    app.wsgi_app = ReverseProxied(app.wsgi_app)

    from status import api as status_blueprint
    app.register_blueprint(status_blueprint, url_prefix='/api')
    from web import api as web_blueprint
    app.register_blueprint(web_blueprint)

    return app

def main():
    '''
    Runs the application
    '''
    app = create_app('COMMON')
    app.run(host=app.config['HOST'], port=app.config['PORT'], debug=app.config['DEBUG'])
    return 0

if __name__ == '__main__':
    main()

