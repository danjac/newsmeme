from flaskext.wtf import Form, HiddenField, TextField, RecaptchaField, \
        SubmitField, ValidationError, required, email, url

from flaskext.babel import lazy_gettext as _

from newsmeme.models import User

from .validators import is_username

class OpenIdSignupForm(Form):
    
    next = HiddenField()

    username = TextField(_("Username"), validators=[
                         required(_("Username required")), 
                         is_username])
    
    email = TextField(_("Email address"), validators=[
                      required(message=_("Email address required")), 
                      email(message=_("Valid email address required"))])
    
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

class OpenIdLoginForm(Form):

    next = HiddenField()

    openid = TextField("OpenID", validators=[
                       required(_("OpenID is required")), 
                       url(_("OpenID must be a valid URL"))])

    submit = SubmitField(_("Login"))
 
