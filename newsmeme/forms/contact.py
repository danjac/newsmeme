# -*- coding: utf-8 -*-
from flaskext.wtf import Form, TextField, TextAreaField, SubmitField, \
        required, email

from flaskext.babel import lazy_gettext as _

class ContactForm(Form):

    name = TextField(_("Your name"), validators=[
                     required(message=_('Your name is required'))])

    email = TextField(_("Your email address"), validators=[
                      required(message=_("Email address required")),
                      email(message=_("A valid email address is required"))])

    subject = TextField(_("Subject"), validators=[
                        required(message=_("Subject required"))])

    message = TextAreaField(_("Message"), validators=[
                            required(message=_("Message required"))])

    submit = SubmitField(_("Send"))

class MessageForm(Form):

    subject = TextField(_("Subject"), validators=[
                        required(message=_("Subject required"))])

    message = TextAreaField(_("Message"), validators=[
                            required(message=_("Message required"))])

    submit = SubmitField(_("Send"))


