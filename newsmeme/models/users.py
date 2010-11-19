import hashlib

from datetime import datetime

from werkzeug import generate_password_hash, check_password_hash, \
    cached_property

from flaskext.sqlalchemy import BaseQuery
from flaskext.principal import RoleNeed, UserNeed, Permission

from newsmeme.extensions import db
from newsmeme.permissions import null
from newsmeme.models.types import DenormalizedText

class UserQuery(BaseQuery):

    def from_identity(self, identity):
        """
        Loads user from flaskext.principal.Identity instance and
        assigns permissions from user.

        A "user" instance is monkeypatched to the identity instance.

        If no user found then None is returned.
        """

        try:
            user = self.get(int(identity.name))
        except ValueError:
            user = None

        if user:
            identity.provides.update(user.provides)

        identity.user = user

        return user
 
    def authenticate(self, login, password):
        
        user = self.filter(db.or_(User.username==login,
                                  User.email==login)).first()

        if user:
            authenticated = user.check_password(password)
        else:
            authenticated = False

        return user, authenticated

    def authenticate_openid(self, email, openid):

        user = self.filter(User.email==email).first()

        if user:
            authenticated = user.check_openid(openid)
        else:
            authenticated = False

        return user, authenticated


class User(db.Model):
    
    __tablename__ = "users"

    query_class = UserQuery

    # user roles
    MEMBER = 100
    MODERATOR = 200
    ADMIN = 300

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.Unicode(60), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    karma = db.Column(db.Integer, default=0)
    date_joined = db.Column(db.DateTime, default=datetime.utcnow)
    activation_key = db.Column(db.String(80), unique=True)
    role = db.Column(db.Integer, default=MEMBER)
    receive_email = db.Column(db.Boolean, default=False)
    email_alerts = db.Column(db.Boolean, default=False)
    followers = db.Column(DenormalizedText)
    following = db.Column(DenormalizedText)

    _password = db.Column("password", db.String(80))
    _openid = db.Column("openid", db.String(80), unique=True)

    class Permissions(object):

        def __init__(self, obj):
            self.obj = obj

        @cached_property
        def send_message(self):
            if not self.obj.receive_email:
                return null

            needs = [UserNeed(user_id) for user_id in self.obj.friends]
            if not needs:
                return null

            return Permission(*needs)

    def __init__(self, *args, **kwargs):
        super(User, self).__init__(*args, **kwargs)
        self.followers = self.followers or set()
        self.following = self.following or set()

    def __str__(self):
        return self.username

    def __repr__(self):
        return "<%s>" % self

    @cached_property
    def permissions(self):
        return self.Permissions(self)

    def _get_password(self):
        return self._password

    def _set_password(self, password):
        self._password = generate_password_hash(password)

    password = db.synonym("_password", 
                          descriptor=property(_get_password,
                                              _set_password))

    def check_password(self, password):
        if self.password is None:
            return False
        return check_password_hash(self.password, password)

    def _get_openid(self):
        return self._openid

    def _set_openid(self, openid):
        self._openid = generate_password_hash(openid)

    openid = db.synonym("_openid", 
                          descriptor=property(_get_openid,
                                              _set_openid))

    def check_openid(self, openid):
        if self.openid is None:
            return False
        return check_password_hash(self.openid, openid)

    @cached_property
    def provides(self):
        needs = [RoleNeed('authenticated'),
                 UserNeed(self.id)]

        if self.is_moderator:
            needs.append(RoleNeed('moderator'))

        if self.is_admin:
            needs.append(RoleNeed('admin'))

        return needs

    @cached_property
    def num_followers(self):
        if self.followers:
            return len(self.followers)
        return 0

    @cached_property
    def num_following(self):
        return len(self.following)

    def is_following(self, user):
        return user.id in self.following

    @property
    def friends(self):
        return self.following.intersection(self.followers)

    def is_friend(self, user):
        return user.id in self.friends

    def get_friends(self):
        return User.query.filter(User.id.in_(self.friends))

    def follow(self, user):
        
        user.followers.add(self.id)
        self.following.add(user.id)

    def unfollow(self, user):
        if self.id in user.followers:
            user.followers.remove(self.id)

        if user.id in self.following:
            self.following.remove(user.id)

    def get_following(self):
        """
        Return following users as query
        """
        return User.query.filter(User.id.in_(self.following or set()))

    def get_followers(self):
        """
        Return followers as query
        """
        return User.query.filter(User.id.in_(self.followers or set()))

    @property
    def is_moderator(self):
        return self.role >= self.MODERATOR

    @property
    def is_admin(self):
        return self.role >= self.ADMIN

    @cached_property
    def gravatar(self):
        if not self.email:
            return ''
        md5 = hashlib.md5()
        md5.update(self.email.strip().lower())
        return md5.hexdigest()

    def gravatar_url(self, size=80):
        if not self.gravatar:
            return ''

        return "http://www.gravatar.com/avatar/%s.jpg?s=%d" % (
            self.gravatar, size)

 
