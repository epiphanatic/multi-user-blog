from google.appengine.ext import db


class Like(db.Model):
    post_id = db.StringProperty(required=True)
    liked_by_id = db.StringProperty(required=True)
    liked = db.BooleanProperty(required=True)