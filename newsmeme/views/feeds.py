
from datetime import datetime

from flask import Module, request, url_for

from werkzeug.contrib.atom import AtomFeed

from newsmeme.models import User, Post, Tag
from newsmeme.helpers import cached

feeds = Module(__name__)

class PostFeed(AtomFeed):

    def add_post(self, post):

        self.add(post.title,
                 unicode(post.markdown),
                 content_type="html",
                 author=post.author.username,
                 url=post.permalink,
                 updated=datetime.utcnow(),
                 published=post.date_created)


@feeds.route("/")
@cached()
def index():
    feed = PostFeed("newsmeme - hot",
                    feed_url=request.url,
                    url=request.url_root)

    posts = Post.query.hottest().public().limit(15)

    for post in posts:
        feed.add_post(post)

    return feed.get_response()


@feeds.route("/latest/")
@cached()
def latest():
    feed = PostFeed("newsmeme - new",
                    feed_url=request.url,
                    url=request.url_root)

    posts = Post.query.public().limit(15)

    for post in posts:
        feed.add_post(post)

    return feed.get_response()


@feeds.route("/deadpool/")
@cached()
def deadpool():
    feed = PostFeed("newsmeme - deadpool",
                    feed_url=request.url,
                    url=request.url_root)

    posts = Post.query.deadpooled().public().limit(15)

    for post in posts:
        feed.add_post(post)

    return feed.get_response()


@feeds.route("/tag/<slug>/")
@cached()
def tag(slug):

    tag = Tag.query.filter_by(slug=slug).first_or_404()

    feed = PostFeed("newsmeme - %s"  % tag,
                    feed_url=request.url,
                    url=request.url_root)

    posts = tag.posts.public().limit(15)

    for post in posts:
        feed.add_post(post)

    return feed.get_response()


@feeds.route("/user/<username>/")
@cached()
def user(username):
    user = User.query.filter_by(username=username).first_or_404()

    feed = PostFeed("newsmeme - %s" % user.username,
                    feed_url=request.url,
                    url=request.url_root)
    
    posts = Post.query.filter_by(author_id=user.id).public().limit(15)
    
    for post in posts:
        feed.add_post(post)

    return feed.get_response()
    
