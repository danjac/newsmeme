# -*- coding: utf-8 -*-
"""
    config.py
    ~~~~~~~~~~~

    Default configuration

    :copyright: (c) 2010 by Dan Jacob.
    :license: BSD, see LICENSE for more details.
"""

from newsmeme import views

class DefaultConfig(object):
    """
    Default configuration for a newsmeme application.
    """

    DEBUG = True

    # change this in your production settings !!!

    SECRET_KEY = "secret"

    # keys for localhost. Change as appropriate.

    RECAPTCHA_PUBLIC_KEY = '6LeYIbsSAAAAACRPIllxA7wvXjIE411PfdB2gt2J'
    RECAPTCHA_PRIVATE_KEY = '6LeYIbsSAAAAAJezaIq3Ft_hSTo0YtyeFG-JgRtu'

    SQLALCHEMY_DATABASE_URI = "sqlite:///newsmeme.db"

    SQLALCHEMY_ECHO = False

    MAIL_DEBUG = DEBUG

    ADMINS = ()

    DEFAULT_MAIL_SENDER = "support@thenewsmeme.com"

    ACCEPT_LANGUAGES = ['en', 'fi']

    DEBUG_LOG = 'logs/debug.log'
    ERROR_LOG = 'logs/error.log'

    THEME = 'newsmeme'

    CACHE_TYPE = "simple"
    CACHE_DEFAULT_TIMEOUT = 300


class TestConfig(object):

    TESTING = True
    CSRF_ENABLED = False
    SQLALCHEMY_DATABASE_URI = "sqlite://"
    SQLALCHEMY_ECHO = False




