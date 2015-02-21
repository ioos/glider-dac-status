from flask.ext.script import Manager
from app import app


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

if __name__ == '__main__':
    manager.run()
