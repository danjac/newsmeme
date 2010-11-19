# -*- coding: utf-8 -*-
"""
    test_models.py
    ~~~~~~~~

    newsmeme tests

    :copyright: (c) 2010 by Dan Jacob.
    :license: BSD, see LICENSE for more details.
"""

from flaskext.sqlalchemy import get_debug_queries
from flaskext.principal import Identity, AnonymousIdentity

from newsmeme import signals
from newsmeme.models import User, Post, Comment, Tag, post_tags
from newsmeme.extensions import db

from tests import TestCase

class TestTags(TestCase):

    def test_empty_tag_cloud(self):

        tags = Tag.query.cloud()

        assert tags == []

    def test_tag_cloud_with_posts(self):

        user = User(username="tester",
                    email="tester@example.com",
                    password="test")

        db.session.add(user)
        db.session.commit()
        
        for i in xrange(20):
            post = Post(author=user,
                        title="test",
                        tags = "Music, comedy, IT crowd")


            db.session.add(post)
            db.session.commit()

        for i in xrange(10):
            post = Post(author=user,
                        title="test",
                        tags = "Twitter, YouTube, funny")

            db.session.add(post)
            db.session.commit()

        post = Post(author=user,
                    title="test",
                    tags="Beer, parties, kegs")

        db.session.add(post)
        db.session.commit()

        assert Tag.query.count() == 9

        tags = Tag.query.cloud()

        for tag in tags:

            if tag.name in ("it crowd", "music", "comedy"):
                assert tag.size == 10

            elif tag.name in ("twitter", "youtube", "funny"):
                assert tag.size == 5

            elif tag.name in ("beer", "parties", "kegs"):
                assert tag.size == 1


class TestUser(TestCase):

    def test_gravatar(self):

        user = User()

        assert user.gravatar == ''

        user = User(email="tester@example.com")

        assert user.gravatar == "f40aca99b2ca1491dbf6ec55597c4397"

    def test_gravatar_url(self):

        user = User()

        assert user.gravatar_url(80) == ''

        user = User(email="tester@example.com")

        assert user.gravatar_url(80) == \
            "http://www.gravatar.com/avatar/f40aca99b2ca1491dbf6ec55597c4397.jpg?s=80"

    def test_following(self):

        user = User()

        assert user.following == set()

        user.following = set([1])

        assert user.following == set([1])
        

    def test_get_following(self):

        user = User(username="tester",
                    email="tester@example.com")

        db.session.add(user)
        
        assert user.get_following().count() == 0

        user2 = User(username="tester2",
                     email="tester2@example.com")

        db.session.add(user2)

        db.session.commit() 

        user.following = set([user2.id])

        assert user.get_following().count() == 1
        assert user.get_following().first().id == user2.id

        assert user.is_following(user2)

    def test_follow(self):

        user = User(username="tester",
                    email="tester@example.com")

        db.session.add(user)
        
        assert user.get_following().count() == 0

        user2 = User(username="tester2",
                     email="tester2@example.com")

        db.session.add(user2)

        assert user2.get_followers().count() == 0

        db.session.commit() 

        user.follow(user2)
        
        db.session.commit()

        assert user.get_following().count() == 1
        assert user.get_following().first().id == user2.id

        assert user2.get_followers().count() == 1
        assert user2.get_followers().first().id == user.id

    def test_unfollow(self):

        user = User(username="tester",
                    email="tester@example.com")

        db.session.add(user)
        
        assert user.get_following().count() == 0

        user2 = User(username="tester2",
                     email="tester2@example.com")

        db.session.add(user2)

        assert user2.get_followers().count() == 0

        db.session.commit() 

        user.follow(user2)
        
        db.session.commit()

        assert user.get_following().count() == 1
        assert user.get_following().first().id == user2.id

        assert user2.get_followers().count() == 1
        assert user2.get_followers().first().id == user.id

        user.unfollow(user2)

        db.session.commit()

        assert user.get_following().count() == 0
        assert user2.get_followers().count() == 0

    def test_can_receive_mail(self):
        
        user = User(username="tester",
                    email="tester@example.com")

        db.session.add(user)
        
        assert user.get_following().count() == 0

        user2 = User(username="tester2",
                     email="tester2@example.com")

        db.session.add(user2)

        db.session.commit()

        id1 = Identity(user.id)
        id2 = Identity(user2.id)

        id1.provides.update(user.provides)
        id2.provides.update(user2.provides)

        assert not user.permissions.send_message.allows(id2)
        assert not user2.permissions.send_message.allows(id1)

        user.follow(user2)

        db.session.commit()

        del user.permissions
        del user2.permissions

        assert not user.permissions.send_message.allows(id2)
        assert not user2.permissions.send_message.allows(id1)

        user2.follow(user)
        user.receive_email = True

        del user.permissions
        del user2.permissions

        assert user.permissions.send_message.allows(id2)
        assert not user2.permissions.send_message.allows(id1)

        user2.receive_email = True

        del user.permissions
        del user2.permissions

        assert user.permissions.send_message.allows(id2)
        assert user2.permissions.send_message.allows(id1)

        user.unfollow(user2)

        del user.permissions
        del user2.permissions

        assert not user.permissions.send_message.allows(id2)
        assert not user2.permissions.send_message.allows(id1)

    def test_is_friend(self):
        
        user = User(username="tester",
                    email="tester@example.com")

        db.session.add(user)
        
        assert user.get_following().count() == 0

        user2 = User(username="tester2",
                     email="tester2@example.com")

        db.session.add(user2)

        db.session.commit()

        assert not user.is_friend(user2)
        assert not user2.is_friend(user)

        user.follow(user2)

        db.session.commit()

        assert not user.is_friend(user2)
        assert not user2.is_friend(user)


    def test_is_friend(self):
        
        user = User(username="tester",
                    email="tester@example.com")

        db.session.add(user)
        
        assert user.get_following().count() == 0

        user2 = User(username="tester2",
                     email="tester2@example.com")

        db.session.add(user2)

        db.session.commit()

        assert not user.is_friend(user2)
        assert not user2.is_friend(user)

        user.follow(user2)

        db.session.commit()

        assert not user.is_friend(user2)
        assert not user2.is_friend(user)

        user2.follow(user)

        assert user.is_friend(user2)
        assert user2.is_friend(user)


    
    def test_get_friends(self):

        user = User(username="tester",
                    email="tester@example.com")

        db.session.add(user)
        
        assert user.get_friends().count() == 0

        user2 = User(username="tester2",
                     email="tester2@example.com")

        db.session.add(user2)

        assert user2.get_friends().count() == 0

        db.session.commit()

        assert not user.is_friend(user2)
        assert not user2.is_friend(user)

        assert user.get_friends().count() == 0
        assert user2.get_friends().count() == 0

        user.follow(user2)

        db.session.commit()

        assert not user.is_friend(user2)
        assert not user2.is_friend(user)

        assert user.get_friends().count() == 0
        assert user2.get_friends().count() == 0

        user2.follow(user)

        assert user.is_friend(user2)
        assert user2.is_friend(user) 

        assert user.get_friends().count() == 1
        assert user2.get_friends().count() == 1

        assert user.get_friends().first().id == user2.id
        assert user2.get_friends().first().id == user.id

    def test_followers(self):

        user = User()

        assert user.followers == set()

        user.followers = set([1])

        assert user.followers == set([1])

    def test_get_followers(self):

        user = User(username="tester",
                    email="tester@example.com")

        db.session.add(user)
        
        assert user.get_followers().count() == 0

        user2 = User(username="tester2",
                     email="tester2@example.com")

        db.session.add(user2)

        db.session.commit() 

        user.followers = set([user2.id])

        assert user.get_followers().count() == 1
        assert user.get_followers().first().id == user2.id

    def test_check_password_if_password_none(self):

        user = User()

        assert not user.check_password("test")

    def test_check_openid_if_password_none(self):

        user = User()

        assert not user.check_openid("test")

    def test_check_password(self):

        user = User(password="test")
        assert user.password != "test"

        assert not user.check_password("test!")
        assert user.check_password("test")

    def test_check_openid(self):

        user = User(openid="google")
        assert user.openid != "google"

        assert not user.check_openid("test")
        assert user.check_openid("google")

    def test_authenticate_no_user(self):

        user, is_auth = User.query.authenticate("tester@example.com", 
                                                "test")

        assert (user, is_auth) == (None, False)

    def test_authenticate_bad_password(self):

        user = User(username=u"tester",
                    email="tester@example.com",
                    password="test!")

        db.session.add(user)
        db.session.commit()

        auth_user, is_auth = \
            User.query.authenticate("tester@example.com", 
                                    "test")

        assert auth_user.id == user.id
        assert not is_auth

    def test_authenticate_good_username(self):

        user = User(username=u"tester",
                    email="tester@example.com",
                    password="test!")

        db.session.add(user)
        db.session.commit()

        auth_user, is_auth = \
            User.query.authenticate("tester", 
                                    "test!")

        assert auth_user.id == user.id
        assert is_auth

    def test_authenticate_good_email(self):

        user = User(username=u"tester",
                    email="tester@example.com",
                    password="test!")
        
        db.session.add(user)
        db.session.commit()

        auth_user, is_auth = \
            User.query.authenticate("tester@example.com", 
                                    "test!")

        assert auth_user.id == user.id
        assert is_auth


class TestPost(TestCase):

    def setUp(self):
        super(TestPost, self).setUp()

        self.user = User(username="tester",
                         email="tester@example.com",
                         password="testing")
        
        db.session.add(self.user)

        self.post = Post(title="testing",
                         link="http://reddit.com",
                         author=self.user)

        db.session.add(self.post)

        db.session.commit()

    def test_url(self):

        assert self.post.url == "/post/1/s/testing/"

    def test_permanlink(self):

        assert self.post.permalink == "http://localhost/post/1/s/testing/"

    def test_popular(self):

        assert Post.query.popular().count() == 1
        self.post.score = 0
        db.session.commit()
        assert Post.query.popular().count() == 0

    def test_deadpooled(self):

        assert Post.query.deadpooled().count() == 0
        self.post.score = 0
        db.session.commit()
        assert Post.query.deadpooled().count() == 1

    def test_jsonify(self):

        d = self.post.json
        assert d['title'] == self.post.title

        json = list(Post.query.jsonify())

        assert json[0]['title'] == self.post.title

    def test_tags(self):

        assert self.post.taglist == []

        self.post.tags = "Music, comedy, IT crowd"

        db.session.commit()

        assert self.post.taglist == ["Music", "comedy", "IT crowd"]
        
        assert self.post.linked_taglist == [
            ("Music", "/tags/music/"),
            ("comedy", "/tags/comedy/"),
            ("IT crowd", "/tags/it-crowd/"),
        ]


        assert Tag.query.count() == 3

        for tag in Tag.query.all():

            assert tag.num_posts == 1
            assert tag.posts[0].id == self.post.id

        post = Post(title="testing again",
                    link="http://reddit.com/r/programming",
                    author=self.user,
                    tags="comedy, it Crowd, Ubuntu")

        db.session.add(post)
        db.session.commit()

        assert post.taglist == ["comedy", "it Crowd", "Ubuntu"]
        assert Tag.query.count() == 4

        for tag in Tag.query.all():

            if tag.name.lower() in ("comedy", "it crowd"):
                assert tag.num_posts == 2
                assert tag.posts.count() == 2

            else:
                assert tag.num_posts == 1
                assert tag.posts.count() == 1

    def test_restricted(self):

        db.session.delete(self.post)

        user = User(username="testing", email="test@example.com")

        db.session.add(user)

        user2 = User(username="tester2", email="test2@example.com")

        db.session.add(user2)
    
        db.session.commit()
        
        admin = User(username="admin", 
                     email="admin@example.com", 
                     role=User.MODERATOR)

        
        assert user.id

        post = Post(title="test",
                    author=user,
                    access=Post.PRIVATE)

        db.session.add(post)
        db.session.commit()

        posts = Post.query.restricted(user)

        assert Post.query.restricted(user).count() == 1
        assert Post.query.restricted(admin).count() == 1
        assert Post.query.restricted(None).count() == 0
        assert Post.query.restricted(user2).count() == 0

        post.access = Post.PUBLIC
        db.session.commit()
    
        posts = Post.query.restricted(user)

        assert Post.query.restricted(user).count() == 1
        assert Post.query.restricted(admin).count() == 1
        assert Post.query.restricted(None).count() == 1
        assert Post.query.restricted(user2).count() == 1
        
        post.access = Post.FRIENDS

        db.session.commit()
        
        assert Post.query.restricted(user).count() == 1
        assert Post.query.restricted(admin).count() == 1
        assert Post.query.restricted(None).count() == 0
        assert Post.query.restricted(user2).count() == 0
    
        user2.follow(user)
        user.follow(user2)

        db.session.commit()

        assert Post.query.restricted(user2).count() == 1

    def test_can_access(self):

        user = User(username="testing", email="test@example.com")

        db.session.add(user)

        user2 = User(username="tester2", email="test2@example.com")

        db.session.add(user2)
    
        db.session.commit()
        
        admin = User(username="admin", 
                     email="admin@example.com", 
                     role=User.MODERATOR)

        
        post = Post(title="test",
                    author_id=user.id,
                    access=Post.PRIVATE)


        assert post.can_access(user)
        assert post.can_access(admin)

        assert not post.can_access(user2)
        assert not post.can_access(None)

        post.access = Post.PUBLIC

        assert post.can_access(user)
        assert post.can_access(admin)

        assert post.can_access(user2)
        assert post.can_access(None)

        post.access = Post.FRIENDS

        assert post.can_access(user)
        assert post.can_access(admin)

        assert not post.can_access(user2)
        assert not post.can_access(None)

        user.follow(user2)
        user2.follow(user)

        assert post.can_access(user2)

    def test_edit_tags(self):

        self.post.tags = "Music, comedy, IT crowd"

        db.session.commit()

        assert self.post.taglist == ["Music", "comedy", "IT crowd"]
        
        assert self.post.linked_taglist == [
            ("Music", "/tags/music/"),
            ("comedy", "/tags/comedy/"),
            ("IT crowd", "/tags/it-crowd/"),
        ]

        def _count_post_tags():
            s = db.select([db.func.count(post_tags)])
            return db.engine.execute(s).scalar()

        assert _count_post_tags() == 3

        self.post.tags = "music, iPhone, books"
        db.session.commit()

        for t in Tag.query.all():
            if t.name in ("music", "iphone", "books"):
                assert t.num_posts == 1
            
            if t.name in ("comedy", "it crowd"):
                assert t.num_posts == 0

        assert _count_post_tags() == 3
        
        self.post.tags = ""

        assert _count_post_tags() == 0

    def test_update_num_comments(self):

        comment = Comment(post=self.post,
                          author=self.user,
                          comment="test")

        db.session.add(comment)
        db.session.commit()

        signals.comment_added.send(self.post)

        post = Post.query.get(self.post.id)

        assert post.num_comments == 1

        db.session.delete(comment)
        db.session.commit()

        signals.comment_deleted.send(post)

        post = Post.query.get(post.id)

        assert post.num_comments == 0

    def test_votes(self):

        assert self.post.votes == set([])
        user = User(username="tester2",
                    email="tester2@example.com")

        db.session.add(user)
        db.session.commit()
        
        self.post.vote(user)

        assert user.id in self.post.votes

        post = Post.query.get(self.post.id)
        assert user.id in post.votes

    def test_can_vote(self):

        assert not self.post.permissions.vote.allows(AnonymousIdentity())

        identity = Identity(self.user.id)
        identity.provides.update(self.user.provides)
        assert not self.post.permissions.vote.allows(identity)

        user = User(username="tester2",
                    email="tester2@gmail.com")

        db.session.add(user)
        db.session.commit()

        identity = Identity(user.id)
        identity.provides.update(user.provides)

        assert self.post.permissions.vote.allows(identity)

        votes = self.post.votes
        votes.add(user.id)
        self.post.votes = votes

        del self.post.permissions

        assert not self.post.permissions.vote.allows(identity)

    def test_can_edit(self):

        assert not self.post.permissions.edit.allows(AnonymousIdentity())

        identity = Identity(self.user.id)
        identity.provides.update(self.user.provides)
        assert self.post.permissions.edit.allows(identity)

        user = User(username="tester2",
                    email="tester2@gmail.com")

        db.session.add(user)
        db.session.commit()

        identity = Identity(user.id)
        assert not self.post.permissions.edit.allows(identity)

        user.role = User.MODERATOR

        identity.provides.update(user.provides)
        assert self.post.permissions.edit.allows(identity)

        user.role = User.ADMIN
        del user.provides

        identity.provides.update(user.provides)
        assert self.post.permissions.edit.allows(identity)

    def test_can_delete(self):

        assert not self.post.permissions.delete.allows(AnonymousIdentity())

        identity = Identity(self.user.id)
        identity.provides.update(self.user.provides)
        assert self.post.permissions.delete.allows(identity)

        user = User(username="tester2",
                    email="tester2@gmail.com")

        db.session.add(user)
        db.session.commit()

        identity = Identity(user.id)
        assert not self.post.permissions.delete.allows(identity)

        user.role = User.MODERATOR

        identity.provides.update(user.provides)
        assert self.post.permissions.delete.allows(identity)

        user.role = User.ADMIN
        del user.provides

        identity.provides.update(user.provides)
        assert self.post.permissions.delete.allows(identity)

    def test_search(self):

        posts = Post.query.search("testing")
        assert posts.count() == 1

        posts = Post.query.search("reddit")
        assert posts.count() == 1

        posts = Post.query.search("digg")
        assert posts.count() == 0

        posts = Post.query.search("testing reddit")
        assert posts.count() == 1

        posts = Post.query.search("testing digg")
        assert posts.count() == 0
    
        posts = Post.query.search("tester")
        assert posts.count() == 1

    def test_get_comments(self):

        parent = Comment(comment="parent comment",
                         author=self.user,
                         post=self.post)


        child1 = Comment(parent=parent,
                         post=self.post,
                         author=self.user,
                         comment="child1")

        child2 = Comment(parent=parent,
                         post=self.post,
                         author=self.user,
                         comment="child2")

        child3 = Comment(parent=child1,
                         post=self.post, 
                         author=self.user,
                         comment="child3")

        db.session.add_all([parent, child1, child2, child3])
        db.session.commit()

        num_queries = len(get_debug_queries())

        comments = self.post.comments

        assert len(get_debug_queries()) == num_queries + 1

        assert comments[0].id == parent.id
        assert comments[0].depth == 0
        
        comments = comments[0].comments

        assert comments[0].id == child1.id
        assert comments[1].id == child2.id

        assert comments[0].depth == 1

        comments = comments[0].comments

        assert comments[0].id == child3.id

        assert comments[0].depth == 2

class TestComment(TestCase):

    def setUp(self):
        super(TestComment, self).setUp()

        self.user = User(username="tester",
                         email="tester@example.com",
                         password="testing")
        
        db.session.add(self.user)

        self.post = Post(title="testing",
                         link="http://reddit.com",
                         author=self.user)

        db.session.add(self.post)

        self.comment = Comment(post=self.post,
                               author=self.user,
                               comment="a comment")

        db.session.add(self.comment)

        db.session.commit()

    def test_restricted(self):

        db.session.delete(self.post)
        db.session.delete(self.comment)

        user = User(username="testing", email="test@example.com")

        db.session.add(user)

        user2 = User(username="tester2", email="test2@example.com")

        db.session.add(user2)
    
        db.session.commit()
        
        admin = User(username="admin", 
                     email="admin@example.com", 
                     role=User.MODERATOR)

        

        post = Post(title="test",
                    author=user,
                    access=Post.PRIVATE)

        db.session.add(post)
        db.session.commit()


        comment = Comment(author=user,
                          post=post,
                          comment="test")


        db.session.add(comment)
        db.session.commit()

        assert Comment.query.restricted(user).count() == 1
        assert Comment.query.restricted(admin).count() == 1
        assert Comment.query.restricted(None).count() == 0
        assert Comment.query.restricted(user2).count() == 0

        post.access = Post.PUBLIC
        db.session.commit()
    
        posts = Post.query.restricted(user)

        assert Comment.query.restricted(user).count() == 1
        assert Comment.query.restricted(admin).count() == 1
        assert Comment.query.restricted(None).count() == 1
        assert Comment.query.restricted(user2).count() == 1
        
        post.access = Post.FRIENDS

        db.session.commit()
        
        assert Comment.query.restricted(user).count() == 1
        assert Comment.query.restricted(admin).count() == 1
        assert Comment.query.restricted(None).count() == 0
        assert Comment.query.restricted(user2).count() == 0
    
        user2.follow(user)
        user.follow(user2)

        db.session.commit()

        assert Comment.query.restricted(user2).count() == 1


    def test_can_edit(self):

        assert not self.comment.permissions.edit.allows(AnonymousIdentity())

        identity = Identity(self.user.id)
        identity.provides.update(self.user.provides)
        assert self.comment.permissions.edit.allows(identity)

        user = User(username="tester2",
                    email="tester2@gmail.com")

        db.session.add(user)
        db.session.commit()

        identity = Identity(user.id)
        assert not self.comment.permissions.edit.allows(identity)

        user.role = User.MODERATOR

        identity.provides.update(user.provides)
        assert self.comment.permissions.edit.allows(identity)

        user.role = User.ADMIN
        del user.provides

        identity.provides.update(user.provides)
        assert self.comment.permissions.edit.allows(identity)


    def test_can_delete(self):

        assert not self.comment.permissions.delete.allows(AnonymousIdentity())

        identity = Identity(self.user.id)
        identity.provides.update(self.user.provides)
        assert self.comment.permissions.delete.allows(identity)

        user = User(username="tester2",
                    email="tester2@gmail.com")

        db.session.add(user)
        db.session.commit()

        identity = Identity(user.id)
        assert not self.comment.permissions.delete.allows(identity)

        user.role = User.MODERATOR

        identity.provides.update(user.provides)
        assert self.comment.permissions.delete.allows(identity)

        user.role = User.ADMIN
        del user.provides

        identity.provides.update(user.provides)
        assert self.comment.permissions.delete.allows(identity)

    def test_votes(self):

        comment = Comment()
        user = User(username="test", 
                    email="test@example.com")

        db.session.add(user)
        db.session.commit()

        assert comment.votes == set([])

        comment.vote(user)

        assert user.id in comment.votes

    def test_can_vote(self):
        assert not self.comment.permissions.vote.allows(AnonymousIdentity())

        identity = Identity(self.user.id)
        identity.provides.update(self.user.provides)
        assert not self.comment.permissions.vote.allows(identity)

        user = User(username="tester2",
                    email="tester2@gmail.com")

        db.session.add(user)
        db.session.commit()

        identity = Identity(user.id)
        identity.provides.update(user.provides)

        assert self.comment.permissions.vote.allows(identity)

        votes = self.comment.votes
        votes.add(user.id)
        self.comment.votes = votes

        del self.comment.permissions

        assert not self.comment.permissions.vote.allows(identity)


    def test_url(self):

        assert self.comment.url == "/post/1/s/testing/#comment-1"

    def test_permanlink(self):

        assert self.comment.permalink == \
                "http://localhost/post/1/s/testing/#comment-1"

