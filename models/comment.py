from google.appengine.ext import db


class Comment(db.Model):
    comment = db.StringProperty(required=True)
    post_id = db.StringProperty(required=True)
    created = db.DateTimeProperty(auto_now_add=True)
    last_modified = db.DateTimeProperty(auto_now=True)
    created_by_id = db.StringProperty(required=True)
    created_by_uname = db.StringProperty(required=True)