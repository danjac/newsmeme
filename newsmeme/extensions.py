from flaskext.mail import Mail
from flaskext.openid import OpenID
from flaskext.sqlalchemy import SQLAlchemy
from flaskext.cache import Cache

__all__ = ['oid', 'mail', 'db']

oid = OpenID()
mail = Mail()
db = SQLAlchemy()
cache = Cache()

