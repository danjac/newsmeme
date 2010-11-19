import functools

from flask import g

def keep_login_url(func):
    """
    Adds attribute g.keep_login_url in order to pass the current
    login URL to login/signup links.
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        g.keep_login_url = True
        return func(*args, **kwargs)
    return wrapper

