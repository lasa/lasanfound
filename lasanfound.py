import webapp2
import jinja2
import logging
import cgi
import os
import time
import string
import sys
import urllib2

from datetime import datetime, timedelta
from google.appengine.ext import db

## see http://jinja.pocoo.org/docs/api/#autoescaping
def guess_autoescape(template_name):
 if template_name is None or '.' not in template_name:
  return False
  ext = template_name.rsplit('.', 1)[1]
  return ext in ('xml', 'html', 'htm')

JINJA_ENVIRONMENT = jinja2.Environment(
 autoescape=guess_autoescape,     ## see http://jinja.pocoo.org/docs/api/#autoxscaping
 loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
 extensions=['jinja2.ext.autoescape'])

class Handler(webapp2.RequestHandler):
 def write(self, *items):    
  self.response.write(" : ".join(items))

 def render_str(self, template, **params):
  tplt = JINJA_ENVIRONMENT.get_template('templates/'+template)
  return tplt.render(params)

 def render(self, template, **kw):
  self.write(self.render_str(template, **kw))

 def render_json(self, d):
  json_txt = json.dumps(d, indent = 3, sort_keys = True)
  self.response.headers['Content-Type'] = 'application/json; charset=UTF-8'
  self.write(json_txt)
#****** DONT EDIT ABOVE THIS LINE *****

#Model for the item objects
class Item(db.Model):
 title = db.StringProperty()
 description = db.StringProperty()
 location = db.StringProperty()
 created = db.DateTimeProperty(auto_now_add = True)

class Home(Handler):
 def get(self):
  logging.info("********** WelcomePage GET **********")
  items = db.GqlQuery("SELECT * FROM Item ORDER BY created DESC limit 10")
  self.render("home.html", items=items)

class NewItem(Handler):
 def get(self):
  logging.info("******** New Item GET ******")
  self.render("newitem.html")

 def post(self):
  logging.info("******** New Item POST *******")
  title = self.request.get("title")
  desc = self.request.get("description")
  location = self.request.get("location")
  it = Item(title=title, description=desc, location=location)
  it.put()
  self.redirect('/')

class About(Handler):
  def get(self):
    logging.info("enter about get")
    self.render("about.html")

application = webapp2.WSGIApplication([
 ('/', Home),
 ('/new', NewItem),
 ('/about', About),
], debug=True)
