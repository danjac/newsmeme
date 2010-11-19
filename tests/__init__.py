# -*- coding: utf-8 -*-
"""
    __init__.py
    ~~~~~~~~

    NewsMeme tests

    :copyright: (c) 2010 by Dan Jacob.
    :license: BSD, see LICENSE for more details.
"""
from flask import g
from flaskext.testing import TestCase as Base, Twill
from flaskext.principal import identity_changed, Identity, AnonymousIdentity

from newsmeme import create_app
from newsmeme.config import TestConfig
from newsmeme.models import User, Post, Comment
from newsmeme.extensions import db

class TestCase(Base):
    
    """
    Base TestClass for your application.
    """

    def create_app(self):
        app = create_app(TestConfig())
        self.twill = Twill(app, port=3000)
        return app
    
    def setUp(self):
        db.create_all()
        g.identity = AnonymousIdentity()

    def tearDown(self):
        db.session.remove()
        db.drop_all()

    def assert_401(self, response):
        assert response.status_code == 401

    def login(self, **kwargs):
        response = self.client.post("/acct/login/", data=kwargs)
        assert response.status_code in (301, 302)

    def logout(self):
        response = self.client.get("/auth/logout/")


