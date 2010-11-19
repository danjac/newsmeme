import random

from datetime import datetime

from werkzeug import cached_property

from flask import url_for, Markup
from flaskext.sqlalchemy import BaseQuery
from flaskext.principal import Permission, UserNeed, Denial

from newsmeme.extensions import db
from newsmeme.helpers import slugify, domain, markdown
from newsmeme.permissions import auth, moderator
from newsmeme.models.types import DenormalizedText
from newsmeme.models.users import User

class PostQuery(BaseQuery):

    def jsonify(self):
        for post in self.all():
            yield post.json

    def as_list(self):
        """
        Return restricted list of columns for list queries
        """

        deferred_cols = ("description", 
                         "tags",
                         "author.email",
                         "author.password",
                         "author.activation_key",
                         "author.openid",
                         "author.date_joined",
                         "author.receive_email",
                         "author.email_alerts",
                         "author.followers",
                         "author.following")


        options = [db.defer(col) for col in deferred_cols]
        return self.options(*options)
        
    def deadpooled(self):
        return self.filter(Post.score <= 0)

    def popular(self):
        return self.filter(Post.score > 0)
    
    def hottest(self):
        return self.order_by(Post.num_comments.desc(),
                             Post.score.desc(),
                             Post.id.desc())

    def public(self):
        return self.filter(Post.access==Post.PUBLIC)

    def restricted(self, user=None):
        """
        Returns posts filtered for a) public posts b) posts authored by
        the user or c) posts authored by friends
        """

        if user and user.is_moderator:
            return self

        criteria = [Post.access==Post.PUBLIC]

        if user:
            criteria.append(Post.author_id==user.id)
            if user.friends:
                criteria.append(db.and_(Post.access==Post.FRIENDS,
                                        Post.author_id.in_(user.friends)))
        
        return self.filter(reduce(db.or_, criteria))

    def search(self, keywords):

        criteria = []

        for keyword in keywords.split():

            keyword = '%' + keyword + '%'

            criteria.append(db.or_(Post.title.ilike(keyword),
                                   Post.description.ilike(keyword),
                                   Post.link.ilike(keyword),
                                   Post.tags.ilike(keyword),
                                   User.username.ilike(keyword)))


        q = reduce(db.and_, criteria)
        
        return self.filter(q).join(User).distinct()


class Post(db.Model):

    __tablename__ = "posts"
    
    PUBLIC = 100
    FRIENDS = 200
    PRIVATE = 300

    PER_PAGE = 40

    query_class = PostQuery

    id = db.Column(db.Integer, primary_key=True)

    author_id = db.Column(db.Integer, 
                          db.ForeignKey(User.id, ondelete='CASCADE'), 
                          nullable=False)
    
    title = db.Column(db.Unicode(200))
    description = db.Column(db.UnicodeText)
    link = db.Column(db.String(250))
    date_created = db.Column(db.DateTime, default=datetime.utcnow)
    score = db.Column(db.Integer, default=1)
    num_comments = db.Column(db.Integer, default=0)
    votes = db.Column(DenormalizedText)
    access = db.Column(db.Integer, default=PUBLIC)

    _tags = db.Column("tags", db.UnicodeText)

    author = db.relation(User, innerjoin=True, lazy="joined")
    
    __mapper_args__ = {'order_by' : id.desc()}

    class Permissions(object):

        def __init__(self, obj):
            self.obj = obj

        @cached_property
        def default(self):
            return Permission(UserNeed(self.obj.author_id)) & moderator

        @cached_property
        def view(self):
            if self.obj.access == Post.PUBLIC:
                return Permission()

            if self.obj.access == Post.FRIENDS:
                needs = [UserNeed(user_id) for user_id in \
                            self.obj.author.friends]

                return self.default & Permission(*needs)

            return self.default

        @cached_property
        def edit(self):
            return self.default

        @cached_property
        def delete(self):
            return self.default

        @cached_property
        def vote(self):

            needs = [UserNeed(user_id) for user_id in self.obj.votes]
            needs.append(UserNeed(self.obj.author_id))

            return auth & Denial(*needs)

        @cached_property
        def comment(self):
            return auth

    def __init__(self, *args, **kwargs):
        super(Post, self).__init__(*args, **kwargs)
        self.votes = self.votes or set()
        self.access = self.access or self.PUBLIC

    def __str__(self):
        return self.title

    def __repr__(self):
        return "<%s>" % self

    @cached_property
    def permissions(self):
        return self.Permissions(self)

    def vote(self, user):
        self.votes.add(user.id)

    def _get_tags(self):
        return self._tags 

    def _set_tags(self, tags):
        
        self._tags = tags

        if self.id:
            # ensure existing tag references are removed
            d = db.delete(post_tags, post_tags.c.post_id==self.id)
            db.engine.execute(d)

        for tag in set(self.taglist):

            slug = slugify(tag)

            tag_obj = Tag.query.filter(Tag.slug==slug).first()
            if tag_obj is None:
                tag_obj = Tag(name=tag, slug=slug)
                db.session.add(tag_obj)
            
            if self not in tag_obj.posts:
                tag_obj.posts.append(self)

    tags = db.synonym("_tags", descriptor=property(_get_tags, _set_tags))

    @property
    def taglist(self):
        if self.tags is None:
            return []

        tags = [t.strip() for t in self.tags.split(",")]
        return [t for t in tags if t]

    @cached_property
    def linked_taglist(self):
        """
        Returns the tags in the original order and format, 
        with link to tag page
        """
        return [(tag, url_for('frontend.tag', 
                              slug=slugify(tag))) \
                for tag in self.taglist]

    @cached_property
    def domain(self):
        if not self.link:
            return ''
        return domain(self.link)

    @cached_property
    def json(self):
        """
        Returns dict of safe attributes for passing into 
        a JSON request.
        """
        
        return dict(post_id=self.id,
                    score=self.score,
                    title=self.title,
                    link=self.link,
                    description=self.description,
                    num_comments=self.num_comments,
                    author=self.author.username)

    @cached_property
    def access_name(self):
        return {
                 Post.PUBLIC : "public",
                 Post.FRIENDS : "friends",
                 Post.PRIVATE : "private"
               }.get(self.access, "public")
        
    def can_access(self, user=None):
        if self.access == self.PUBLIC:
            return True

        if user is None:
            return False

        if user.is_moderator or user.id == self.author_id:
            return True

        return self.access == self.FRIENDS and self.author_id in user.friends

    @cached_property
    def comments(self):
        """
        Returns comments in tree. Each parent comment has a "comments" 
        attribute appended and a "depth" attribute.
        """
        from newsmeme.models.comments import Comment

        comments = Comment.query.filter(Comment.post_id==self.id).all()

        def _get_comments(parent, depth):
            
            parent.comments = []
            parent.depth = depth

            for comment in comments:
                if comment.parent_id == parent.id:
                    parent.comments.append(comment)
                    _get_comments(comment, depth + 1)


        parents = [c for c in comments if c.parent_id is None]

        for parent in parents:
            _get_comments(parent, 0)

        return parents
        
    def _url(self, _external=False):
        return url_for('post.view', 
                       post_id=self.id, 
                       slug=self.slug, 
                       _external=_external)

    @cached_property
    def url(self):
        return self._url()

    @cached_property
    def permalink(self):
        return self._url(True)

    @cached_property
    def markdown(self):
        return Markup(markdown(self.description or ''))

    @cached_property
    def slug(self):
        return slugify(self.title or '')[:80]


post_tags = db.Table("post_tags", db.Model.metadata,
    db.Column("post_id", db.Integer, 
              db.ForeignKey('posts.id', ondelete='CASCADE'), 
              primary_key=True),

    db.Column("tag_id", db.Integer, 
              db.ForeignKey('tags.id', ondelete='CASCADE'),
              primary_key=True))


class TagQuery(BaseQuery):

    def cloud(self):

        tags = self.filter(Tag.num_posts > 0).all()

        if not tags:
            return []

        max_posts = max(t.num_posts for t in tags)
        min_posts = min(t.num_posts for t in tags)

        diff = (max_posts - min_posts) / 10.0
        if diff < 0.1:
            diff = 0.1

        for tag in tags:
            tag.size = int(tag.num_posts / diff)
            if tag.size < 1: 
                tag.size = 1

        random.shuffle(tags)

        return tags


class Tag(db.Model):

    __tablename__ = "tags"
    
    query_class = TagQuery

    id = db.Column(db.Integer, primary_key=True)
    slug = db.Column(db.Unicode(80), unique=True)
    posts = db.dynamic_loader(Post, secondary=post_tags, query_class=PostQuery)

    _name = db.Column("name", db.Unicode(80), unique=True)
    
    def __str__(self):
        return self.name

    def _get_name(self):
        return self._name

    def _set_name(self, name):
        self._name = name.lower().strip()
        self.slug = slugify(name)

    name = db.synonym("_name", descriptor=property(_get_name, _set_name))

    @cached_property
    def url(self):
        return url_for("frontend.tag", slug=self.slug)

    num_posts = db.column_property(
        db.select([db.func.count(post_tags.c.post_id)]).\
            where(db.and_(post_tags.c.tag_id==id,
                          Post.id==post_tags.c.post_id,
                          Post.access==Post.PUBLIC)).as_scalar())


