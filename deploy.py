# UWSGI configuration

import uwsgi
import production_settings

from newsmeme import create_app

application = create_app(production_settings)
uwsgi.applications = {"/":application}

