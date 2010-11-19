from flask import Module, abort, jsonify, request,  \
    g, url_for, redirect, flash

from flaskext.mail import Message
from flaskext.babel import gettext as _

from newsmeme import signals
from newsmeme.models import Post, Comment
from newsmeme.forms import CommentForm, PostForm
from newsmeme.helpers import render_template
from newsmeme.decorators import keep_login_url
from newsmeme.extensions import db, mail, cache
from newsmeme.permissions import auth

post = Module(__name__)

@post.route("/<int:post_id>/")
@post.route("/<int:post_id>/s/<slug>/")
@cache.cached(unless=lambda: g.user is not None)
@keep_login_url
def view(post_id, slug=None):
    post = Post.query.get_or_404(post_id)
    if not post.permissions.view:
        if not g.user:
            flash(_("You must be logged in to see this post"), "error")
            return redirect(url_for("account.login", next=request.path))
        else:
            flash(_("You must be a friend to see this post"), "error")
            abort(403)

    def edit_comment_form(comment):
        return CommentForm(obj=comment)

    return render_template("post/post.html", 
                           comment_form=CommentForm(),
                           edit_comment_form=edit_comment_form,
                           post=post)


@post.route("/<int:post_id>/upvote/", methods=("POST",))
@auth.require(401)
def upvote(post_id):
    return _vote(post_id, 1)


@post.route("/<int:post_id>/downvote/", methods=("POST",))
@auth.require(401)
def downvote(post_id):
    return _vote(post_id, -1)


@post.route("/<int:post_id>/addcomment/", methods=("GET", "POST"))
@post.route("/<int:post_id>/<int:parent_id>/reply/", methods=("GET", "POST"))
@auth.require(401)
def add_comment(post_id, parent_id=None):
    post = Post.query.get_or_404(post_id)
    post.permissions.view.test(403)

    parent = Comment.query.get_or_404(parent_id) if parent_id else None
    
    form = CommentForm()

    if form.validate_on_submit():
        comment = Comment(post=post,
                          parent=parent,
                          author=g.user)
        
        form.populate_obj(comment)

        db.session.add(comment)
        db.session.commit()

        signals.comment_added.send(post)

        flash(_("Thanks for your comment"), "success")

        author = parent.author if parent else post.author

        if author.email_alerts and author.id != g.user.id:
            
            subject = _("Somebody replied to your comment") if parent else \
                      _("Somebody commented on your post")

            template = "emails/comment_replied.html" if parent else \
                       "emails/post_commented.html"

            body = render_template(template,
                                   author=author,
                                   post=post,
                                   parent=parent,
                                   comment=comment)

            mail.send_message(subject=subject,
                              body=body,
                              recipients=[post.author.email])


        return redirect(comment.url)
    
    return render_template("post/add_comment.html",
                           parent=parent,
                           post=post,
                           form=form)


@post.route("/<int:post_id>/edit/", methods=("GET", "POST"))
@auth.require(401)
def edit(post_id):

    post = Post.query.get_or_404(post_id)
    post.permissions.edit.test(403)
    
    form = PostForm(obj=post)
    if form.validate_on_submit():

        form.populate_obj(post)
        db.session.commit()

        if g.user.id != post.author_id:
            body = render_template("emails/post_edited.html",
                                   post=post)

            message = Message(subject="Your post has been edited",
                              body=body,
                              recipients=[post.author.email])

            mail.send(message)

            flash(_("The post has been updated"), "success")
        
        else:
            flash(_("Your post has been updated"), "success")
        return redirect(url_for("post.view", post_id=post_id))

    return render_template("post/edit_post.html", 
                           post=post, 
                           form=form)


@post.route("/<int:post_id>/delete/", methods=("POST",))
@auth.require(401)
def delete(post_id):

    post = Post.query.get_or_404(post_id)
    post.permissions.delete.test(403)
    
    Comment.query.filter_by(post=post).delete()

    db.session.delete(post)
    db.session.commit()

    if g.user.id != post.author_id:
        body = render_template("emails/post_deleted.html",
                               post=post)

        message = Message(subject="Your post has been deleted",
                          body=body,
                          recipients=[post.author.email])

        mail.send(message)

        flash(_("The post has been deleted"), "success")
    
    else:
        flash(_("Your post has been deleted"), "success")

    return jsonify(success=True,
                   redirect_url=url_for('frontend.index'))

def _vote(post_id, score):

    post = Post.query.get_or_404(post_id)
    post.permissions.vote.test(403)
    
    post.score += score
    post.author.karma += score

    if post.author.karma < 0:
        post.author.karma = 0

    post.vote(g.user)

    db.session.commit()

    return jsonify(success=True,
                   post_id=post_id,
                   score=post.score)

