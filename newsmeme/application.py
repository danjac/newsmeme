# -*- coding: utf-8 -*-
"""
    application.py
    ~~~~~~~~~~~

    Application configuration

    :copyright: (c) 2010 by Dan Jacob.
    :license: BSD, see LICENSE for more details.
"""
import os
import logging

from logging.handlers import SMTPHandler, RotatingFileHandler

from flask import Flask, Response, request, g, \
        jsonify, redirect, url_for, flash

from flaskext.babel import Babel, gettext as _
from flaskext.themes import setup_themes
from flaskext.principal import Principal, identity_loaded

from newsmeme import helpers
from newsmeme import views
from newsmeme.config import DefaultConfig
from newsmeme.models import User, Tag
from newsmeme.helpers import render_template
from newsmeme.extensions import db, mail, oid, cache

__all__ = ["create_app"]

DEFAULT_APP_NAME = "newsmeme"

DEFAULT_MODULES = (
    (views.frontend, ""),
    (views.post, "/post"),
    (views.user, "/user"),
    (views.comment, "/comment"),
    (views.account, "/acct"),
    (views.feeds, "/feeds"),
    (views.openid, "/openid"),
    (views.api, "/api"),
)

def create_app(config=None, app_name=None, modules=None):

    if app_name is None:
        app_name = DEFAULT_APP_NAME

    if modules is None:
        modules = DEFAULT_MODULES

    app = Flask(app_name)

    configure_app(app, config)

    configure_logging(app)
    configure_errorhandlers(app)
    configure_extensions(app)
    configure_before_handlers(app)
    configure_template_filters(app)
    configure_context_processors(app)
    # configure_after_handlers(app)
    configure_modules(app, modules)

    return app


def configure_app(app, config):
    
    app.config.from_object(DefaultConfig())

    if config is not None:
        app.config.from_object(config)

    app.config.from_envvar('APP_CONFIG', silent=True)


def configure_modules(app, modules):
    
    for module, url_prefix in modules:
        app.register_module(module, url_prefix=url_prefix)


def configure_template_filters(app):

    @app.template_filter()
    def timesince(value):
        return helpers.timesince(value)


def configure_before_handlers(app):

    @app.before_request
    def authenticate():
        g.user = getattr(g.identity, 'user', None)


def configure_context_processors(app):

    @app.context_processor
    def get_tags():
        tags = cache.get("tags")
        if tags is None:
            tags = Tag.query.order_by(Tag.num_posts.desc()).limit(10).all()
            cache.set("tags", tags)

        return dict(tags=tags)

    @app.context_processor
    def config():
        return dict(config=app.config)


def configure_extensions(app):

    mail.init_app(app)
    db.init_app(app)
    oid.init_app(app)
    cache.init_app(app)

    setup_themes(app)

    # more complicated setups

    configure_identity(app)
    configure_i18n(app)
    

def configure_identity(app):

    Principal(app)

    @identity_loaded.connect_via(app)
    def on_identity_loaded(sender, identity):
        g.user = User.query.from_identity(identity)


def configure_i18n(app):

    babel = Babel(app)

    @babel.localeselector
    def get_locale():
        accept_languages = app.config.get('ACCEPT_LANGUAGES', 
                                               ['en_gb'])

        return request.accept_languages.best_match(accept_languages)


def configure_errorhandlers(app):

    if app.testing:
        return

    @app.errorhandler(404)
    def page_not_found(error):
        if request.is_xhr:
            return jsonify(error=_('Sorry, page not found'))
        return render_template("errors/404.html", error=error)

    @app.errorhandler(403)
    def forbidden(error):
        if request.is_xhr:
            return jsonify(error=_('Sorry, not allowed'))
        return render_template("errors/403.html", error=error)

    @app.errorhandler(500)
    def server_error(error):
        if request.is_xhr:
            return jsonify(error=_('Sorry, an error has occurred'))
        return render_template("errors/500.html", error=error)

    @app.errorhandler(401)
    def unauthorized(error):
        if request.is_xhr:
            return jsonfiy(error=_("Login required"))
        flash(_("Please login to see this page"), "error")
        return redirect(url_for("account.login", next=request.path))


def configure_logging(app):
    if app.debug or app.testing:
        return

    mail_handler = \
        SMTPHandler(app.config['MAIL_SERVER'],
                    'error@newsmeme.com',
                    app.config['ADMINS'], 
                    'application error',
                    (
                        app.config['MAIL_USERNAME'],
                        app.config['MAIL_PASSWORD'],
                    ))

    mail_handler.setLevel(logging.ERROR)
    app.logger.addHandler(mail_handler)

    formatter = logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s '
        '[in %(pathname)s:%(lineno)d]')

    debug_log = os.path.join(app.root_path, 
                             app.config['DEBUG_LOG'])

    debug_file_handler = \
        RotatingFileHandler(debug_log,
                            maxBytes=100000,
                            backupCount=10)

    debug_file_handler.setLevel(logging.DEBUG)
    debug_file_handler.setFormatter(formatter)
    app.logger.addHandler(debug_file_handler)

    error_log = os.path.join(app.root_path, 
                             app.config['ERROR_LOG'])

    error_file_handler = \
        RotatingFileHandler(error_log,
                            maxBytes=100000,
                            backupCount=10)

    error_file_handler.setLevel(logging.ERROR)
    error_file_handler.setFormatter(formatter)
    app.logger.addHandler(error_file_handler)



