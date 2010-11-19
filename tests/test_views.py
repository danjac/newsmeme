# -*- coding: utf-8 -*-
"""
    test_views.py
    ~~~~~~~~

    NewsMeme tests

    :copyright: (c) 2010 by Dan Jacob.
    :license: BSD, see LICENSE for more details.
"""

from newsmeme.signals import comment_added
from newsmeme.models import User, Post, Comment
from newsmeme.extensions import db, mail

from tests import TestCase

class TestApi(TestCase):

    def create_user(self):
        user = User(username="tester",
                    email="tester@example.com",
                    password="test")

        db.session.add(user)
        db.session.commit()

        return user

    def create_post(self):
        
        post = Post(author=self.create_user(),
                    title="test")

        db.session.add(post)
        db.session.commit()

        return post

    def test_get_post(self):

        post = self.create_post()

        response = self.client.get("/api/post/%d/" % post.id)
        self.assert_200(response)

        assert response.json['post_id'] == post.id
        assert response.json['title'] == "test"
        assert response.json['author'] == "tester"

    def test_search(self):

        self.create_post()

        response = self.client.get("/api/search/?keywords=test") 

        self.assert_200(response)

        assert len(response.json['results']) == 1

    def test_user(self):

        self.create_post()

        response = self.client.get("/api/user/tester/")
        self.assert_200(response)

        assert len(response.json['posts']) == 1


class TestComment(TestCase):

    def create_comment(self):

        user = User(username="tester",
                    email="tester@example.com",
                    password="test")

        post = Post(author=user,
                    title="test")

        comment = Comment(post=post,
                          author=user,
                          comment="test")

        db.session.add_all([user, post, comment])
        db.session.commit()

        comment_added.send(post)
        return comment

    def test_edit_comment_not_logged_in(self):

        comment = self.create_comment()
        response = self.client.get("/comment/%d/edit/" % comment.id)
        self.assert_401(response)

    def test_edit_comment_not_logged_in_as_author(self):

        comment = self.create_comment()
        user = User(username="tester2",
                    email="tester2@example.com",
                    password="test")

        db.session.add(user)
        db.session.commit()

        self.login(login="tester2", password="test")

        response = self.client.get("/comment/%d/edit/" % comment.id)
        self.assert_403(response)

    def test_edit_comment_logged_in_as_author(self):

        comment = self.create_comment()
        self.login(login="tester", password="test")

        response = self.client.get("/comment/%d/edit/" % comment.id)
        self.assert_200(response)

    def test_update_comment_logged_in_as_author(self):

        comment = self.create_comment()

        self.login(login="tester", password="test")

        response = self.client.post("/comment/%d/edit/" % comment.id,
                                    data={"comment":"test2"})
        
        self.assert_redirects(response, comment.url)
        
        comment = Comment.query.get(comment.id)

        assert comment.comment == "test2"

    def test_delete_comment_not_logged_in(self):

        comment = self.create_comment()
        response = self.client.get("/comment/%d/delete/" % comment.id)
        self.assert_405(response)
       
    def test_delete_comment_not_logged_in_as_author(self):

        comment = self.create_comment()
        response = self.client.post("/comment/%d/delete/" % comment.id)
  
        self.assert_401(response)

        user = User(username="tester2",
                    email="tester2@example.com",
                    password="test")

        db.session.add(user)
        db.session.commit()

        self.login(login="tester2", password="test")

        response = self.client.post("/comment/%d/delete/" % comment.id)
        self.assert_403(response)

    def test_delete_comment_logged_in_as_author(self):

        comment = self.create_comment()
        self.login(login="tester", password="test")

        response = self.client.post("/comment/%d/delete/" % comment.id)
        
        assert Comment.query.count() == 0

        post = Post.query.get(comment.post.id)
        assert post.num_comments == 0

        assert response.json['success']
        assert response.json['comment_id'] == comment.id

    
class TestFrontend(TestCase):

    def test_tags(self):

        user = User(username="tester",
                    email="tester@example.com",
                    password="test")

        db.session.add(user)
        db.session.commit()

        for i in xrange(20):

            post = Post(author=user,
                        tags="IT Crowd, funny, TV",
                        title="test")

            db.session.add(post)
            db.session.commit()
        
        response = self.client.get("/tags/")
        self.assert_200(response)

    def test_rules(self):
        response = self.client.get("/rules/")
        self.assert_200(response)
 
    def test_index(self):
        
        response = self.client.get("/")
        self.assert_200(response)
        
        user = User(username="tester",
                    password="test",
                    email="tester@example.com")

        db.session.add(user)
        
        for i in xrange(100):
            post =  Post(author=user,
                         link="http://reddit.com",
                         title="test post")

            db.session.add(post)

        db.session.commit()

        response = self.client.get("/")
        self.assert_200(response)

    def test_latest(self):

        
        user = User(username="tester",
                    password="test",
                    email="tester@example.com")

        db.session.add(user)
        
        for i in xrange(100):
            post =  Post(author=user,
                         link="http://reddit.com",
                         title="test post")

            db.session.add(post)

        db.session.commit()

    def test_submit_not_logged_in(self):

        response = self.client.get("/submit/")
        self.assert_401(response)

    def test_post_submit_not_logged_in(self):

        data = {
                "title" : "testing",
                "description" : "a test"
                }

        response = self.client.post("/submit/", data=data)
        self.assert_401(response)

    def test_submit_logged_in(self):

        user = User(username="tester",
                    password="test",
                    email="tester@example.com")

        db.session.add(user)
        db.session.commit()

        self.login(login="tester", password="test")
        response = self.client.get("/submit/")
        self.assert_200(response)

    def test_post_submit_logged_in(self):
        
        user = User(username="tester",
                    password="test",
                    email="tester@example.com")

        db.session.add(user)
        db.session.commit()

        self.login(login="tester", password="test")
    
        data = {
                "title" : "testing",
                "description" : "a test"
                }

        response = self.client.post("/submit/", data=data)
        self.assert_redirects(response, "/latest/")

        assert Post.query.count() == 1
        
class TestPost(TestCase):

    def create_user(self, login=False):

        user = User(username="tester",
                    password="test",
                    email="tester@example.com")

        db.session.add(user)
        db.session.commit()

        if login:
            self.login(login="tester", password="test")
        return user

    def test_delete_post_via_get(self):

        response = self.client.get("/post/1/delete/")
        self.assert_405(response)

    def test_delete_non_existing_post_not_logged_in(self):

        response = self.client.post("/post/1/delete/")
        self.assert_401(response)

    def test_delete_non_existing_post_logged_in(self):

        user = self.create_user(True)
        response = self.client.post("/post/1/delete/")
        self.assert_404(response)

    def test_delete_existing_post_not_logged_in(self):

        user = self.create_user(False)
        
        post = Post(author=user,
                    title="test",
                    description="test")

        db.session.add(post)
        db.session.commit()

        response = self.client.post("/post/%d/delete/" % post.id)
        self.assert_401(response)
        
    def test_delete_existing_post_logged_in_as_author(self):

        user = self.create_user(True)
        
        post = Post(author=user,
                    title="test",
                    description="test")

        db.session.add(post)
        db.session.commit()

        response = self.client.post("/post/%d/delete/" % post.id)

        self.assert_200(response)

        assert response.json['success']
        assert Post.query.count() == 0

    def test_delete_post_not_logged_in_as_author(self):

        user = self.create_user(False)
        
        post = Post(author=user,
                    title="test",
                    description="test")

        db.session.add(post)
        db.session.commit()

        user = User(username="tester2",
                    password="test",
                    email="tester2@example.com")

        db.session.add(user)
        db.session.commit()

        self.login(login="tester2", password="test")
 
        response = self.client.post("/post/%d/delete/" % post.id)

        self.assert_403(response)

    def test_delete_post_logged_in_as_admin(self):
    
        user = self.create_user(False)
        
        admin_user = User(username="admin",
                          email="admin@newsmeme.com",
                          password="admin1",
                          role=User.ADMIN)

        db.session.add(admin_user)
        db.session.commit()

        self.login(login="admin", password="admin1")

        post = Post(author=user,
                    title="test",
                    description="test")

        db.session.add(post)
        db.session.commit()

        with mail.record_messages() as outbox:
            response = self.client.post("/post/%d/delete/" % post.id)
        
            assert response.json['success']
            assert Post.query.count() == 0
            assert len(outbox) == 1

    def test_edit_non_existing_post_not_logged_in(self):

        response = self.client.get("/post/1/edit/")
        self.assert_401(response)
        
    def test_edit_non_existing_post_logged_in(self):

        user = self.create_user(True)
        response = self.client.get("/post/1/edit/")
        
        self.assert_404(response)

    def test_edit_existing_post_not_logged_in(self):

        post = Post(author=self.create_user(False),
                    title="test",
                    description="test")

        db.session.add(post)
        db.session.commit()

        response = self.client.get("/post/%d/edit/" % post.id)
        self.assert_401(response)

    def test_edit_existing_post_not_logged_in_as_author(self):

        post = Post(author=self.create_user(False),
                    title="test",
                    description="test")

        db.session.add(post)
        db.session.commit()

        user = User(username="tester2",
                    password="test",
                    email="tester2@example.com")

        db.session.add(user)
        db.session.commit()

        self.login(login="tester2", password="test")
 
        response = self.client.get("/post/%d/edit/" % post.id)
        self.assert_403(response)

    def test_edit_existing_post_logged_in_as_author(self):

        post = Post(author=self.create_user(True),
                    title="test",
                    description="test")

        db.session.add(post)
        db.session.commit()

        response = self.client.get("/post/%d/edit/" % post.id)
        self.assert_200(response)

    def test_update_existing_post_logged_in_as_author(self):

        post = Post(author=self.create_user(True),
                    title="test",
                    description="test")

        db.session.add(post)
        db.session.commit()


        data = {
                "title" : "testing 123",
                "description" : "a test 123"
                }


        response = self.client.post("/post/%d/edit/" % post.id, data=data)
        self.assert_redirects(response, "/post/%d/" % post.id)
        
        post = Post.query.first()

        assert post.title == "testing 123"
        assert post.description == "a test 123"

    def test_update_existing_post_logged_in_as_admin(self):

        post = Post(author=self.create_user(False),
                    title="test",
                    description="test")

        db.session.add(post)
        db.session.commit()

        admin_user = User(username="admin",
                          email="admin@newsmeme.com",
                          password="admin1",
                          role=User.ADMIN)

        db.session.add(admin_user)
        db.session.commit()

        self.login(login="admin", password="admin1")
 
 
        data = {
                "title" : "testing 123",
                "description" : "a test 123"
                }


        with mail.record_messages() as outbox:
            response = self.client.post("/post/%d/edit/" % post.id, data=data)
        
            self.assert_redirects(response, "/post/%d/" % post.id)
            assert len(outbox) == 1

        post = Post.query.first()

        assert post.title == "testing 123"
        assert post.description == "a test 123"
 
    def test_view_post(self):

        response = self.client.get("/post/1/")
        self.assert_404(response)

        user = User(username="tester",
                    password="test",
                    email="tester@example.com")

        db.session.add(user)
        db.session.commit()

        post = Post(author=user,
                    title="test",
                    description="test")

        db.session.add(post)
        db.session.commit()

        response = self.client.get("/post/%d/" % post.id)
        self.assert_200(response)

        for i in xrange(100):
            user = User(username="tester-%d" % i,
                        email="tester=%d.gmail.com" % i,
                        password="test")

            comment = Comment(post=post,
                              author=user,
                              comment="a comment")
            db.session.add(user)
            db.session.add(comment)

        db.session.commit()

        response = self.client.get("/post/%d/" % post.id)
        self.assert_200(response)
    
    def test_add_comment(self):

        response = self.client.get("/post/1/addcomment/")
        self.assert_401(response)

        user = User(username="tester",
                    email="tester@example.com",
                    password="test")

        db.session.add(user)
        db.session.commit()

        self.login(login="tester", password="test")

        response = self.client.get("/post/1/addcomment/")
        self.assert_404(response)

        post = Post(author=user,
                    title="test",
                    link="http://reddit.com")

        db.session.add(post)
        db.session.commit()
        

        response = self.client.get("/post/%d/addcomment/" % post.id)
        self.assert_200(response)

        response = self.client.get("/post/%d/1/reply/" % post.id)

        with mail.record_messages() as outbox:
            response = self.client.post("/post/%d/addcomment/" % post.id,
                data={"comment" : "testing"})
        
            assert len(outbox) == 0

        comment = Comment.query.first()

        self.assert_redirects(response, comment.url)

        # reply to this comment

        response = self.client.get("/post/%d/%d/reply/" % (post.id, comment.id))

        self.assert_200(response)
        
        with mail.record_messages() as outbox:
            response = self.client.post("/post/%d/%d/reply/" % (
                post.id, comment.id), data={'comment':'hello'})

            assert len(outbox) == 0

        assert Comment.query.count() == 2

        reply = Comment.query.filter(
            Comment.parent_id==comment.id).first()

        assert reply.comment == "hello"

        self.assert_redirects(response, reply.url)


        # another user

        user2 = User(username="tester2",
                     email="tester2@example.com",
                     password="test")

        db.session.add(user2)
        db.session.commit()

        self.login(login="tester2", password="test")

        with mail.record_messages() as outbox:
            response = self.client.post("/post/%d/addcomment/" % post.id,
                data={"comment" : "testing"})
        
            assert len(outbox) == 0

        user.email_alerts = True
        db.session.add(user)
        db.session.commit()

        assert User.query.filter(User.email_alerts==True).count() == 1

        with mail.record_messages() as outbox:
            response = self.client.post("/post/%d/addcomment/" % post.id,
                data={"comment" : "testing"})
        
            assert len(outbox) == 1


        with mail.record_messages() as outbox:
            response = self.client.post(
                "/post/%d/%d/reply/" % (post.id, comment.id),
                data={"comment" : "testing"})
        
            assert len(outbox) == 1

        # double check author doesn't receive own emails

        self.login(login="tester", password="test")

        with mail.record_messages() as outbox:
            response = self.client.post("/post/%d/%d/reply/" % (
                post.id, comment.id), data={'comment':'hello'})

            assert len(outbox) == 0


class TestFeeds(TestCase):

    def setUp(self):
        super(TestFeeds, self).setUp()

        user = User(username="tester",
                    email="tester@example.com",
                    password="test")

        db.session.add(user)
        db.session.commit()

        for i in xrange(20):

            post = Post(author=user,
                        tags="programming",
                        title="TESTING",
                        description="test")


            db.session.add(post)
            db.session.commit()

    def test_posts(self):

        response = self.client.get("/feeds/")
        self.assert_200(response)

    def test_latest(self):

        response = self.client.get("/feeds/latest/")
        self.assert_200(response)

    def test_user(self):

        response = self.client.get("/feeds/user/danjac/")
        self.assert_404(response)

        response = self.client.get("/feeds/user/tester/")
        self.assert_200(response)

    def test_tag(self):

        response = self.client.get("/feeds/tag/foo/")
        self.assert_404(response)

        response = self.client.get("/feeds/tag/programming/")
        self.assert_200(response)

class TestAccount(TestCase):

    def test_delete_account(self):

        response = self.client.get("/acct/delete/")
        self.assert_401(response)

        user = User(username="tester",
                    password="test",
                    email="tester@example.com")

        db.session.add(user)
        db.session.commit()

        self.login(login="tester@example.com", password="test")

        response = self.client.get("/acct/delete/")
        self.assert_200(response)

        response = self.client.post("/acct/delete/", 
                                    data={'recaptcha_challenge_field':'test',
                                          'recaptcha_response_field':'test'})
        self.assert_redirects(response, "/")

        assert User.query.count() == 0


    def test_login(self):

        response = self.client.get("/acct/login/")
        self.assert_200(response)

        response = self.client.post("/acct/login/", 
            data={"login" : "tester", "password" : "test"})

        self.assert_200(response)
        assert "invalid login" in response.data

        user = User(username="tester",
                    password="test",
                    email="tester@example.com")

        db.session.add(user)
        db.session.commit()

        response = self.client.post("/acct/login/", 
            data={"login" : "tester", "password" : "test"})

        self.assert_redirects(response, "/user/tester/")

        response = self.client.post("/acct/login/", 
            data={"login" : "tester", "password" : "test",
                  "next" : "/submit/"})

        self.assert_redirects(response, "/submit/")

    def test_logout(self):

        response = self.client.get("/acct/logout/")
        self.assert_redirects(response, "/")


class TestUser(TestCase):

    def setUp(self):
        super(TestUser, self).setUp()

        self.user = User(username="tester", 
                         email="tester@example.com",
                         password="test")

        db.session.add(self.user)

        for i in xrange(10):

            post = Post(author=self.user,
                        title="test")

            db.session.add(post)

            comment = Comment(post=post,
                              author=self.user,
                              comment="test comment")

            db.session.add(comment)

        db.session.commit()

    def test_posts(self):

        response = self.client.get("/user/tester/")
        self.assert_200(response)

    def test_comments(self):

        response = self.client.get("/user/tester/comments/")
        self.assert_200(response)

class TestOpenId(TestCase):

    def test_login(self):

        response = self.client.get("/openid/login/")
        self.assert_200(response)

    def test_signup(self):

        response = self.client.get("/openid/signup/")
        self.assert_403(response)
