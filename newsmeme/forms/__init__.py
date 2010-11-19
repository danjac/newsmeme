# -*- coding: utf-8 -*-
"""
    forms.py
    ~~~~~~~~

    Description of the module goes here...

    :copyright: (c) 2010 by Dan Jacob.
    :license: BSD, see LICENSE for more details.
"""

from .account import LoginForm, SignupForm, EditAccountForm, \
        RecoverPasswordForm, ChangePasswordForm, DeleteAccountForm

from .openid import OpenIdLoginForm, OpenIdSignupForm
from .post import PostForm
from .contact import ContactForm, MessageForm
from .comment import CommentForm, CommentAbuseForm
