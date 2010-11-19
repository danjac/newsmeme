from flask import Module, redirect, url_for, session, flash, \
    abort, request, current_app

from flaskext.babel import gettext as _
from flaskext.principal import Identity, identity_changed

from newsmeme.models import User
from newsmeme.helpers import slugify, render_template
from newsmeme.forms import OpenIdSignupForm, OpenIdLoginForm
from newsmeme.extensions import oid, db

openid = Module(__name__)

@oid.after_login
def create_or_login(response):
    
    openid = response.identity_url

    user, authenticated = \
        User.query.authenticate_openid(response.email, openid)

    next_url = session.pop('next', None)
    
    if user is None:
        session['openid'] = openid
        
        username = response.fullname or response.nickname
        if username:
            username = slugify(username.replace("-", "_"))

        return redirect(url_for("openid.signup", 
                                next=next_url,
                                name=username,
                                email=response.email))

    if authenticated:
        
        session.permanent = True

        identity_changed.send(current_app._get_current_object(),
                              identity=Identity(user.id))
        
        flash(_("Welcome back, %%s") % user.username, "success")
        
        if next_url is None:
            next_url = url_for('user.posts', username=user.username)

        return redirect(next_url)
    
    # user already exists, so login and attach openid
    session['openid'] = openid 

    flash(_("You already have an account with us. "
            "Please login with your email address so your "
            "OpenID can be attached to your user account"), "success")

    return redirect(url_for('account.login', 
                            login=response.email))


@openid.route("/login/", methods=("GET", "POST"))
@oid.loginhandler
def login():
    
    form = OpenIdLoginForm(next=request.args.get("next"))

    if form.validate_on_submit():
        session['next'] = form.next.data

        return oid.try_login(form.openid.data,  
                             ask_for=('email', 'fullname', 'nickname'))

    return render_template("openid/login.html", 
                           form=form,
                           error=oid.fetch_error())


@openid.route("/signup/", methods=("GET", "POST"))
def signup():
    
    if 'openid' not in session:
        abort(403)

    form = OpenIdSignupForm(next=request.args.get("next"),
                            username=request.args.get("name"),
                            email=request.args.get("email"))

    if form.validate_on_submit():

        user = User(openid=session.pop('openid'))
        form.populate_obj(user)

        db.session.add(user)
        db.session.commit()

        session.permanent = True

        identity_changed.send(current_app._get_current_object(),
                              identity=Identity(user.id))

        flash(_("Welcome, %%s") % user.username, "success")

        next_url = form.next.data or \
            url_for("user.posts", username=user.username)
    
        return redirect(next_url)

    return render_template("openid/signup.html", form=form)
