import sys

from fabric.api import env, run, cd

"""
Sample fabric file. Assumes the following on production server:

- virtualenv + virtualenvwrapper
- mercurial
- supervisord (running gunicorn/uwsgi etc.)

Copy and modify as required for your own particular setup.

Keep your private settings in a separate module, fab_settings.py, in
the same directory as this file.
"""

try:
    import fab_settings as settings
except ImportError:
    print "You must provide a valid fab_settings.py module in this directory"
    sys.exit(1)


def server():
    env.hosts = settings.SERVER_HOSTS
    env.user = settings.SERVER_USER
    env.password = settings.SERVER_PASSWORD


def deploy():
    """
    Pulls latest code into staging, runs tests, then pulls into live.
    """
    providers = (server,)
    with cd(settings.STAGING_DIR):
        run("hg pull -u")
        run("workon %s;nosetests" % settings.VIRTUALENV)
    with cd(settings.PRODUCTION_DIR):
        run("hg pull -u")


def reload():
    """
    Deploys and then reloads application server.
    """
    deploy()
    run("supervisorctl -c %s restart %s" % (settings.SUPERVISOR_CONF,
                                            settings.SUPERVISOR_CMD))


def upgrade():
    """
    Updates all required packages, runs tests, then updates packages on
    live, then restarts server.
    """

    with cd(settings.PRODUCTION_DIR):
        run("workon %s; python setup.py develop -U" % settings.VIRTUALENV)

    reload()


