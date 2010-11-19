# -*- coding: utf-8 -*-
from flaskext.wtf import Form, HiddenField, BooleanField, TextField, \
        PasswordField, SubmitField, TextField, RecaptchaField, \
        ValidationError, required, email, equal_to, regexp

from flaskext.babel import gettext, lazy_gettext as _ 

from newsmeme.models import User
from newsmeme.extensions import db

from .validators import is_username

class LoginForm(Form):

    next = HiddenField()
    
    remember = BooleanField(_("Remember me"))
    
    login = TextField(_("Username or email address"), validators=[
                      required(message=\
                               _("You must provide an email or username"))])

    password = PasswordField(_("Password"))

    submit = SubmitField(_("Login"))

class SignupForm(Form):

    next = HiddenField()

    username = TextField(_("Username"), validators=[
                         required(message=_("Username required")), 
                         is_username])

    password = PasswordField(_("Password"), validators=[
                             required(message=_("Password required"))])

    password_again = PasswordField(_("Password again"), validators=[
                                   equal_to("password", message=\
                                            _("Passwords don't match"))])

    email = TextField(_("Email address"), validators=[
                      required(message=_("Email address required")), 
                      email(message=_("A valid email address is required"))])

    recaptcha = RecaptchaField(_("Copy the words appearing below"))

    submit = SubmitField(_("Signup"))

    def validate_username(self, field):
        user = User.query.filter(User.username.like(field.data)).first()
        if user:
            raise ValidationError, gettext("This username is taken")

    def validate_email(self, field):
        user = User.query.filter(User.email.like(field.data)).first()
        if user:
            raise ValidationError, gettext("This email is taken")


class EditAccountForm(Form):

    username = TextField("Username", validators=[
                         required(_("Username is required")), is_username])

    email = TextField(_("Your email address"), validators=[
                      required(message=_("Email address required")),
                      email(message=_("A valid email address is required"))])

    receive_email = BooleanField(_("Receive private emails from friends"))
    
    email_alerts = BooleanField(_("Receive an email when somebody replies "
                                  "to your post or comment"))


    submit = SubmitField(_("Save"))

    def __init__(self, user, *args, **kwargs):
        self.user = user
        kwargs['obj'] = self.user
        super(EditAccountForm, self).__init__(*args, **kwargs)
        
    def validate_username(self, field):
        user = User.query.filter(db.and_(
                                 User.username.like(field.data),
                                 db.not_(User.id==self.user.id))).first()

        if user:
            raise ValidationError, gettext("This username is taken")

    def validate_email(self, field):
        user = User.query.filter(db.and_(
                                 User.email.like(field.data),
                                 db.not_(User.id==self.user.id))).first()
        if user:
            raise ValidationError, gettext("This email is taken")


class RecoverPasswordForm(Form):

    email = TextField("Your email address", validators=[
                      email(message=_("A valid email address is required"))])

    submit = SubmitField(_("Find password"))


class ChangePasswordForm(Form):

    activation_key = HiddenField()

    password = PasswordField("Password", validators=[
                             required(message=_("Password is required"))])
    
    password_again = PasswordField(_("Password again"), validators=[
                                   equal_to("password", message=\
                                            _("Passwords don't match"))])

    submit = SubmitField(_("Save"))


class DeleteAccountForm(Form):
    
    recaptcha = RecaptchaField(_("Copy the words appearing below"))

    submit = SubmitField(_("Delete"))


