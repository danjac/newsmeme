from flask import Module, url_for, \
    redirect, g, flash, request, current_app

from flaskext.mail import Message
from flaskext.babel import gettext as _

from newsmeme.models import Post, Tag
from newsmeme.extensions import mail, db
from newsmeme.helpers import render_template, cached
from newsmeme.forms import PostForm, ContactForm
from newsmeme.decorators import keep_login_url
from newsmeme.permissions import auth

frontend = Module(__name__)

@frontend.route("/")
@frontend.route("/<int:page>/")
@cached()
@keep_login_url
def index(page=1):
    
    page_obj = \
            Post.query.popular().hottest().\
                restricted(g.user).as_list().\
                paginate(page, per_page=Post.PER_PAGE)
        
    page_url = lambda page: url_for("frontend.index", page=page)

    return render_template("index.html", 
                           page_obj=page_obj, 
                           page_url=page_url)


@frontend.route("/latest/")
@frontend.route("/latest/<int:page>/")
@cached()
@keep_login_url
def latest(page=1):
    
    page_obj = \
            Post.query.popular().restricted(g.user).as_list().\
                paginate(page, per_page=Post.PER_PAGE)

    page_url = lambda page: url_for("frontend.latest", page=page)

    return render_template("latest.html", 
                           page_obj=page_obj, 
                           page_url=page_url)


@frontend.route("/deadpool/")
@frontend.route("/deadpool/<int:page>/")
@cached()
@keep_login_url
def deadpool(page=1):
    page_obj = \
            Post.query.deadpooled().restricted(g.user).as_list().\
                paginate(page, per_page=Post.PER_PAGE)

    page_url = lambda page: url_for("frontend.deadpool", page=page)

    return render_template("deadpool.html", 
                           page_obj=page_obj, 
                           page_url=page_url)


@frontend.route("/submit/", methods=("GET", "POST"))
@auth.require(401)
def submit():

    form = PostForm()
    
    if form.validate_on_submit():

        post = Post(author=g.user)
        form.populate_obj(post)

        db.session.add(post)
        db.session.commit()

        flash(_("Thank you for posting"), "success")

        return redirect(url_for("frontend.latest"))

    return render_template("submit.html", form=form)


@frontend.route("/search/")
@frontend.route("/search/<int:page>/")
@keep_login_url
def search(page=1):

    keywords = request.args.get("keywords", '').strip()

    if not keywords:
        return redirect(url_for("frontend.index"))

    page_obj = \
            Post.query.search(keywords).restricted(g.user).\
                as_list().paginate(page, per_page=Post.PER_PAGE)

    if page_obj.total == 1:

        post = page_obj.items[0]
        return redirect(post.url)
    
    page_url = lambda page: url_for('frontend.search', 
                                    page=page,
                                    keywords=keywords)

    return render_template("search.html",
                           page_obj=page_obj,
                           page_url=page_url,
                           keywords=keywords)



@frontend.route("/contact/", methods=("GET", "POST"))
@keep_login_url
def contact():

    if g.user:
        form = ContactForm(name=g.user.username,
                           email=g.user.email)

    else:
        form = ContactForm()

    if form.validate_on_submit():

        admins = current_app.config.get('ADMINS', [])

        from_address = "%s <%s>" % (form.name.data, 
                                    form.email.data)

        if admins:
            message = Message(subject=form.subject.data,
                              body=form.message.data,
                              recipients=admins,
                              sender=from_address)

            mail.send(message)
        
        flash(_("Thanks, your message has been sent to us"), "success")

        return redirect(url_for('frontend.index'))

    return render_template("contact.html", form=form)


@frontend.route("/tags/")
@cached()
@keep_login_url
def tags():
    tags = Tag.query.cloud()
    return render_template("tags.html", tag_cloud=tags)


@frontend.route("/tags/<slug>/")
@frontend.route("/tags/<slug>/<int:page>/")
@cached()
@keep_login_url
def tag(slug, page=1):
    tag = Tag.query.filter_by(slug=slug).first_or_404()

    page_obj = tag.posts.restricted(g.user).as_list().\
                    paginate(page, per_page=Post.PER_PAGE)

    page_url = lambda page: url_for('frontend.tag',
                                    slug=slug,
                                    page=page)

    return render_template("tag.html", 
                           tag=tag,
                           page_url=page_url,
                           page_obj=page_obj)
    

@frontend.route("/help/")
@keep_login_url
def help():
    return render_template("help.html")


@frontend.route("/rules/")
@keep_login_url
def rules():
    return render_template("rules.html")
