import sys
import os
import site

sys.stdin = sys.stdout

site.addsitedir("/home/danjac354/.virtualenvs/newsmeme/lib/python2.7/site-packages")

BASE_DIR = os.path.join(os.path.dirname(__file__))
sys.path.append(BASE_DIR)

import production_settings

from newsmeme import create_app

application = create_app(production_settings)
