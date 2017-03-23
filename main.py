import os
import re
import hmac
from models import Comment, User, Like, Post

import webapp2
import jinja2

from google.appengine.ext import db

template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader=jinja2.FileSystemLoader(template_dir),
                               autoescape=True)

secret = 'supersecretsquirrel'


def render_str(template, **params):
    t = jinja_env.get_template(template)
    return t.render(params)


def make_secure_val(val):
    return '%s|%s' % (val, hmac.new(secret, val).hexdigest())


def check_secure_val(secure_val):
    val = secure_val.split('|')[0]
    if secure_val == make_secure_val(val):
        return val


class BlogHandler(webapp2.RequestHandler):
    def write(self, *a, **kw):
        self.response.out.write(*a, **kw)

    def render_str(self, template, **params):
        params['user'] = self.user
        return render_str(template, **params)

    def render(self, template, **kw):
        self.write(self.render_str(template, **kw))

    def set_secure_cookie(self, name, val):
        cookie_val = make_secure_val(val)
        self.response.headers.add_header(
            'Set-Cookie',
            '%s=%s; Path=/' % (name, cookie_val))

    def read_secure_cookie(self, name):
        cookie_val = self.request.cookies.get(name)
        return cookie_val and check_secure_val(cookie_val)

    def login(self, user):
        self.set_secure_cookie('user_id', str(user.key().id()))

    def logout(self):
        self.response.headers.add_header('Set-Cookie', 'user_id=; Path=/')

    def initialize(self, *a, **kw):
        webapp2.RequestHandler.initialize(self, *a, **kw)
        uid = self.read_secure_cookie('user_id')
        self.user = uid and User.by_id(int(uid))


def render_post(response, post):
    response.out.write('<b>' + post.subject + '</b><br>')
    response.out.write(post.content)


# existence checking decorator functions

def post_exists(function):
    def wrapper(self, post_id):
        key = db.Key.from_path('Post', int(post_id), parent=blog_key())
        post = db.get(key)
        if post:
            return function(self, post_id, post)
        else:
            self.redirect('/')
            return
    return wrapper


def comment_exists(function):
    def wrapper(self, comment_id):
        key = db.Key.from_path('Comment', int(comment_id), parent=blog_key())
        comment = db.get(key)
        if comment:
            return function(self, comment_id, comment)
        else:
            self.redirect('/')
            return
    return wrapper


# user checks decorator functions

def user_logged_in(function):
    def wrapper(self):
        if self.user:
            return function(self)
        else:
            self.redirect('/login')
            return
    return wrapper


# blog stuff

def blog_key(name='default'):
    return db.Key.from_path('blogs', name)


class BlogFront(BlogHandler):
    def get(self):
        posts = Post.all().order('-created')
        error = self.request.get('error')
        self.render('front.html', posts=posts, error=error)


class PostPage(BlogHandler):
    @post_exists
    def get(self, post_id, post):
        post = post

        if not post:
            self.error(404)
            return

        self.render("permalink.html", post=post)


class NewPost(BlogHandler):
    @user_logged_in
    def get(self):
        self.render("newpost.html")

    @user_logged_in
    def post(self):
        subject = self.request.get('subject')
        content = self.request.get('content')
        created_by_id = str(self.user.key().id())
        created_by_uname = self.user.name

        if subject and content:
            p = Post(parent=blog_key(), subject=subject, content=content,
                     created_by_id=created_by_id,
                     created_by_uname=created_by_uname)
            p.put()
            self.redirect('/blog/%s' % str(p.key().id()))
        else:
            error = "subject and content, please!"
            self.render("newpost.html", subject=subject, content=content,
                        error=error)


class EditPostHandler(BlogHandler):
    @post_exists
    def get(self, post_id, post):
        if self.user:
            user_id = self.user.key().id()
            post = post

            if str(post.created_by_id) == str(user_id):
                self.render("editpost.html", user_id=user_id, post=post)
            else:
                error = "wronguser"
                self.redirect("/blog?error=%s" % error)
        else:
            self.redirect("/login")

    @post_exists
    def post(self, post_id, post):
        if self.user:
            user_id = self.user.key().id()
            post = post
            subject = self.request.get('subject')
            content = self.request.get('content')

            if str(post.created_by_id) == str(user_id):
                if subject and content:
                    post.subject = subject
                    post.content = content
                    post.put()
                    self.redirect('/blog/%s' % str(post.key().id()))

                else:
                    error = "subject and content cannot be blank!"
                    self.render("editpost.html", post=post, error=error)
            else:
                error = "wronguser"
                self.redirect("/blog?error=%s" % error)
        else:
            self.redirect('/blog')


class DeletePostHandler(BlogHandler):
    @post_exists
    def get(self, post_id, post):
        if self.user:
            user_id = self.user.key().id()
            post = post

            if str(post.created_by_id) == str(user_id):
                post.delete()
                self.render("deletepost.html", post=post)
            else:
                error = "wronguser"
                self.redirect("/blog?error=%s" % error)
        else:
            self.redirect('/login')


class CommentPostHandler(BlogHandler):
    @post_exists
    def get(self, post_id, post):
        if self.user:
            post = post
            self.render("commentpost.html", post=post)

        else:
            self.redirect('/login')

    @post_exists
    def post(self, post_id, post):
        if self.user:
            comment = self.request.get('comment')
            created_by_id = str(self.user.key().id())
            created_by_uname = self.user.name
            post_id = post_id
            post = post

            if comment:
                c = Comment(parent=blog_key(), post_id=post_id,
                            comment=comment,
                            created_by_id=created_by_id,
                            created_by_uname=created_by_uname)
                c.put()
                self.redirect('/blog/%s' % str(post_id))
            else:
                error = "comment cannot be blank!"
                self.render("commentpost.html", post=post, error=error)
        else:
            self.redirect("/login")


class EditCommentHandler(BlogHandler):
    @comment_exists
    def get(self, comment_id, comment):
        if self.user:
            user_id = self.user.key().id()
            comment = comment
            if str(comment.created_by_id) == str(user_id):
                self.render("editcomment.html", user_id=user_id,
                            comment=comment)
            else:
                error = "wronguser"
                self.redirect("/blog?error=%s" % error)
        else:
            self.redirect("/login")

    @comment_exists
    def post(self, comment_id, comment):
        if self.user:
            user_id = self.user.key().id()
            comment = comment
            comment_content = self.request.get('comment')

            if str(comment.created_by_id) == str(user_id):
                if comment_content:
                    comment.comment = comment_content
                    comment.put()
                    self.redirect('/blog/%s' % str(comment.post_id))

                else:
                    error = "comment cannot be blank!"
                    self.render("editcomment.html", comment=comment,
                                error=error)
            else:
                error = "wronguser"
                self.redirect("/blog?error=%s" % error)
        else:
            self.redirect('/blog')


class DeleteCommentHandler(BlogHandler):
    @comment_exists
    def get(self, comment_id, comment):
        if self.user:
            user_id = self.user.key().id()
            comment = comment

            if str(comment.created_by_id) == str(user_id):
                comment.delete()
                self.render("deletecomment.html", comment=comment)
            else:
                error = "wronguser"
                self.redirect("/blog?error=%s" % error)
        else:
            self.redirect('/login')


class LikePostHandler(BlogHandler):
    @post_exists
    def get(self, post_id, post):
        if self.user:
            user_id = str(self.user.key().id())
            post = post

            user_like = db.GqlQuery("select * from Like where post_id = '%s' "
                                    "and liked_by_id ='%s'" %
                                    (post_id, user_id))

            # if the current user is not the one who made the post:
            if str(post.created_by_id) != str(user_id):
                # if they haven't already liked the post
                if user_like.count() > 0:
                    error = "sameuser"
                    self.redirect("/blog?error=%s" % error)
                else:
                    like = Like(parent=blog_key(), post_id=post_id, liked=True,
                                liked_by_id=user_id)
                    like.put()
                    self.redirect('/blog/%s' % str(post_id))
            else:
                error = "wronguser"
                self.redirect("/blog?error=%s" % error)
        else:
            self.redirect('/login')


class UnLikePostHandler(BlogHandler):
    @post_exists
    def get(self, post_id, post):
        if self.user:
            user_id = str(self.user.key().id())
            post = post

            user_likes = db.GqlQuery("select * from Like where post_id = '%s' "
                                     "and liked_by_id ='%s'" %
                                     (post_id, user_id))

            # if the current user is not the one who made the post:
            if str(post.created_by_id) != str(user_id):
                    for like in user_likes:
                        likeKey = db.Key.from_path('Like', like.key().id(),
                                                   parent=blog_key())
                        like_obj = db.get(likeKey)
                        like_obj.delete()

                    self.redirect('/blog/%s' % str(post_id))
            else:
                error = "wronguser"
                self.redirect("/blog?error=%s" % error)
        else:
            self.redirect('/login')


# validity checks

USER_RE = re.compile(r"^[a-zA-Z0-9_-]{3,20}$")


def valid_username(username):
    return username and USER_RE.match(username)

PASS_RE = re.compile(r"^.{3,20}$")


def valid_password(password):
    return password and PASS_RE.match(password)

EMAIL_RE = re.compile(r'^[\S]+@[\S]+\.[\S]+$')


def valid_email(email):
    return not email or EMAIL_RE.match(email)


# Registration and authentication

class Signup(BlogHandler):
    def get(self):
        self.render("signup-form.html")

    def post(self):
        have_error = False
        self.username = self.request.get('username')
        self.password = self.request.get('password')
        self.verify = self.request.get('verify')
        self.email = self.request.get('email')

        params = dict(username=self.username,
                      email=self.email)

        if not valid_username(self.username):
            params['error_username'] = "That's not a valid username."
            have_error = True

        if not valid_password(self.password):
            params['error_password'] = "That wasn't a valid password."
            have_error = True
        elif self.password != self.verify:
            params['error_verify'] = "Your passwords didn't match."
            have_error = True

        if not valid_email(self.email):
            params['error_email'] = "That's not a valid email."
            have_error = True

        if have_error:
            self.render('signup-form.html', **params)
        else:
            self.done()

    def done(self, *a, **kw):
        raise NotImplementedError


class Register(Signup):
    def done(self):
        # make sure the user doesn't already exist
        u = User.by_name(self.username)
        if u:
            msg = 'That user already exists.'
            self.render('signup-form.html', error_username=msg)
        else:
            u = User.register(self.username, self.password, self.email)
            u.put()

            self.login(u)
            self.redirect('/welcome')


class Login(BlogHandler):
    def get(self):
        self.render('login-form.html')

    def post(self):
        username = self.request.get('username')
        password = self.request.get('password')

        u = User.login(username, password)
        if u:
            self.login(u)
            self.redirect('/blog')
        else:
            msg = 'Invalid login'
            self.render('login-form.html', error=msg)


class Logout(BlogHandler):
    def get(self):
        self.logout()
        self.redirect('/blog')


class Welcome(BlogHandler):
    def get(self):
        if self.user:
            self.render('welcome.html', username=self.user.name)
        else:
            self.redirect('/signup')


app = webapp2.WSGIApplication([('/', BlogFront),
                               ('/blog/?', BlogFront),
                               ('/blog/([0-9]+)', PostPage),
                               ('/blog/newpost', NewPost),
                               ('/signup', Register),
                               ('/login', Login),
                               ('/logout', Logout),
                               ('/welcome', Welcome),
                               ('/blog/editcomment/([0-9]+)',
                                EditCommentHandler),
                               ('/blog/deletecomment/([0-9]+)',
                                DeleteCommentHandler),
                               ('/blog/editpost/([0-9]+)', EditPostHandler),
                               ('/blog/deletepost/([0-9]+)',
                                DeletePostHandler),
                               ('/blog/likepost/([0-9]+)',
                                LikePostHandler),
                               ('/blog/unlikepost/([0-9]+)',
                                UnLikePostHandler),
                               ('/blog/commentpost/([0-9]+)',
                                CommentPostHandler)
                               ],
                              debug=True)
