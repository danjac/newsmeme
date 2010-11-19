# -*- coding: utf-8 -*-
"""
    manage.py
    ~~~~~~~~~

    Description of the module goes here...

    :copyright: (c) 2010 by Dan Jacob.
    :license: BSD, see LICENSE for more details.
"""
import sys
import feedparser

from flask import current_app

from flaskext.script import Manager, prompt, prompt_pass, \
    prompt_bool, prompt_choices

from flaskext.mail import Message

from newsmeme import create_app
from newsmeme.extensions import db, mail
from newsmeme.models import Post, User, Comment, Tag

manager = Manager(create_app)

@manager.option("-u", "--url", dest="url", help="Feed URL")
@manager.option("-n", "--username", dest="username", help="Save to user")
def importfeed(url, username):
    """
    Bulk import news from a feed. For testing only !
    """

    user = User.query.filter_by(username=username).first()
    if not user:
        print "User %s does not exist" % username
        sys.exit(1)
    d = feedparser.parse(url)
    for entry in d['entries']:
        post = Post(author=user,
                    title=entry.title[:200],
                    link=entry.link)

        db.session.add(post)
    db.session.commit()

@manager.option('-u', '--username', dest="username", required=False)
@manager.option('-p', '--password', dest="password", required=False)
@manager.option('-e', '--email', dest="email", required=False)
@manager.option('-r', '--role', dest="role", required=False)
def createuser(username=None, password=None, email=None, role=None):
    """
    Create a new user
    """
    
    if username is None:
        while True:
            username = prompt("Username")
            user = User.query.filter(User.username==username).first()
            if user is not None:
                print "Username %s is already taken" % username
            else:
                break

    if email is None:
        while True:
            email = prompt("Email address")
            user = User.query.filter(User.email==email).first()
            if user is not None:
                print "Email %s is already taken" % email
            else:
                break

    if password is None:
        password = prompt_pass("Password")

        while True:
            password_again = prompt_pass("Password again")
            if password != password_again:
                print "Passwords do not match"
            else:
                break
    
    roles = (
        (User.MEMBER, "member"),
        (User.MODERATOR, "moderator"),
        (User.ADMIN, "admin"),
    )

    if role is None:
        role = prompt_choices("Role", roles, resolve=int, default=User.MEMBER)

    user = User(username=username,
                email=email,
                password=password,
                role=role)

    db.session.add(user)
    db.session.commit()

    print "User created with ID", user.id


@manager.command
def createall():
    "Creates database tables"
    
    db.create_all()

@manager.command
def dropall():
    "Drops all database tables"
    
    if prompt_bool("Are you sure ? You will lose all your data !"):
        db.drop_all()

@manager.command
def mailall():
    "Sends an email to all users"
    
    subject = prompt("Subject")
    message = prompt("Message")
    from_address = prompt("From", default="support@thenewsmeme.com")
    if prompt_bool("Are you sure ? Email will be sent to everyone!"):
        with mail.connect() as conn:
            for user in User.query:
                message = Message(subject=subject,
                                  body=message,
                                  sender=from_address,
                                  recipients=[user.email])

                conn.send(message)


@manager.shell
def make_shell_context():
    return dict(app=current_app, 
                db=db,
                Post=Post,
                User=User,
                Tag=Tag,
                Comment=Comment)


manager.add_option('-c', '--config',
                   dest="config",
                   required=False,
                   help="config file")

if __name__ == "__main__":
    manager.run()
