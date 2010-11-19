import uuid

from flask import Module, flash, request, g, current_app, \
    abort, redirect, url_for, session, jsonify

from flaskext.mail import Message
from flaskext.babel import gettext as _
from flaskext.principal import identity_changed, Identity, AnonymousIdentity

from newsmeme.forms import ChangePasswordForm, EditAccountForm, \
    DeleteAccountForm, LoginForm, SignupForm, RecoverPasswordForm

from newsmeme.models import User
from newsmeme.helpers import render_template
from newsmeme.extensions import db, mail
from newsmeme.permissions import auth

account = Module(__name__)

@account.route("/login/", methods=("GET", "POST"))
def login():

    form = LoginForm(login=request.args.get("login", None),
                     next=request.args.get("next", None))

    # TBD: ensure "next" field is passed properly

    if form.validate_on_submit():
        user, authenticated = \
            User.query.authenticate(form.login.data,
                                    form.password.data)

        if user and authenticated:
            session.permanent = form.remember.data
            
            identity_changed.send(current_app._get_current_object(),
                                  identity=Identity(user.id))

            # check if openid has been passed in
            openid = session.pop('openid', None)
            if openid:
                user.openid = openid
                db.session.commit()
                
                flash(_("Your OpenID has been attached to your account. "
                      "You can now sign in with your OpenID."), "success")


            else:
                flash(_("Welcome back, %(name)s", name=user.username), "success")

            next_url = form.next.data

            if not next_url or next_url == request.path:
                next_url = url_for('user.posts', username=user.username)

            return redirect(next_url)

        else:

            flash(_("Sorry, invalid login"), "error")

    return render_template("account/login.html", form=form)

@account.route("/signup/", methods=("GET", "POST"))
def signup():

    form = SignupForm(next=request.args.get("next"))

    if form.validate_on_submit():
        
        user = User()
        form.populate_obj(user)

        db.session.add(user)
        db.session.commit()

        identity_changed.send(current_app._get_current_object(),
                              identity=Identity(user.id))

        flash(_("Welcome, %(name)s", name=user.username), "success")

        next_url = form.next.data

        if not next_url or next_url == request.path:
            next_url = url_for('user.posts', username=user.username)

        return redirect(next_url)

    return render_template("account/signup.html", form=form)


@account.route("/logout/")
def logout():

    flash(_("You are now logged out"), "success")
    identity_changed.send(current_app._get_current_object(),
                          identity=AnonymousIdentity())

    return redirect(url_for('frontend.index'))


@account.route("/forgotpass/", methods=("GET", "POST"))
def forgot_password():

    form = RecoverPasswordForm()

    if form.validate_on_submit():

        user = User.query.filter_by(email=form.email.data).first()
        
        if user:
            flash(_("Please see your email for instructions on "
                  "how to access your account"), "success")
            
            user.activation_key = str(uuid.uuid4())
            db.session.commit()

            body = render_template("emails/recover_password.html",
                                   user=user)

            message = Message(subject=_("Recover your password"),
                              body=body,
                              recipients=[user.email])

            mail.send(message)
            
            return redirect(url_for("frontend.index"))

        else:

            flash(_("Sorry, no user found for that email address"), "error")

    return render_template("account/recover_password.html", form=form)


@account.route("/changepass/", methods=("GET", "POST"))
def change_password():

    user = None

    if g.user:
        user = g.user

    elif 'activation_key' in request.values:
        user = User.query.filter_by(
            activation_key=request.values['activation_key']).first()
    
    if user is None:
        abort(403)

    form = ChangePasswordForm(activation_key=user.activation_key)

    if form.validate_on_submit():

        user.password = form.password.data
        user.activation_key = None

        db.session.commit()

        flash(_("Your password has been changed, "
                "please log in again"), "success")

        return redirect(url_for("account.login"))

    return render_template("account/change_password.html", form=form)
        

@account.route("/edit/", methods=("GET", "POST"))
@auth.require(401)
def edit():
    
    form = EditAccountForm(g.user)

    if form.validate_on_submit():

        form.populate_obj(g.user)
        db.session.commit()

        flash(_("Your account has been updated"), "success")

        return redirect(url_for("frontend.index"))

    return render_template("account/edit_account.html", form=form)


@account.route("/delete/", methods=("GET", "POST"))
@auth.require(401)
def delete():

    # confirm password & recaptcha
    form = DeleteAccountForm()

    if form.validate_on_submit():

        db.session.delete(g.user)
        db.session.commit()
    
        identity_changed.send(current_app._get_current_object(),
                              identity=AnonymousIdentity())

        flash(_("Your account has been deleted"), "success")

        return redirect(url_for("frontend.index"))

    return render_template("account/delete_account.html", form=form)


@account.route("/follow/<int:user_id>/", methods=("POST",))
@auth.require(401)
def follow(user_id):
    
    user = User.query.get_or_404(user_id)
    g.user.follow(user)
    db.session.commit()

    body = render_template("emails/followed.html",
                           user=user)

    mail.send_message(subject=_("%s is now following you" % g.user.username),
                      body=body,
                      recipients=[user.email])

    return jsonify(success=True,
                   reload=True)


@account.route("/unfollow/<int:user_id>/", methods=("POST",))
@auth.require(401)
def unfollow(user_id):
    
    user = User.query.get_or_404(user_id)
    g.user.unfollow(user)
    db.session.commit()

    return jsonify(success=True,
                   reload=True)

