from flask.ext.script import Manager
from app import app


manager = Manager(app)

@manager.command
def get_status():
    from status.tasks import get_dac_status
    result = get_dac_status.delay()
    result.wait()

if __name__ == '__main__':
    manager.run()
