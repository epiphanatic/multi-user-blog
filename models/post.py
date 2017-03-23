import os
from google.appengine.ext import db
import jinja2


template_dir = os.path.join(os.path.dirname(__file__), '../templates')
jinja_env = jinja2.Environment(loader=jinja2.FileSystemLoader(template_dir),
                               autoescape=True)


def render_str(template, **params):
    t = jinja_env.get_template(template)
    return t.render(params)


class Post(db.Model):
    subject = db.StringProperty(required=True)
    content = db.TextProperty(required=True)
    created = db.DateTimeProperty(auto_now_add=True)
    last_modified = db.DateTimeProperty(auto_now=True)
    created_by_id = db.StringProperty(required=True)
    created_by_uname = db.StringProperty(required=True)

    def render(self):
        post_id = str(self.key().id())
        comments = db.GqlQuery("select * from Comment where post_id = '%s' "
                               "order by created desc" % post_id)
        likes = db.GqlQuery("select * from Like where post_id = '%s'" %
                            post_id)

        self._render_text = self.content.replace('\n', '<br>')
        return render_str("post.html", p=self, comments=comments, likes=likes)