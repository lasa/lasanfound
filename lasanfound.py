import webapp2
import jinja2
import logging
import cgi
import os
import time
import string
import sys
import urllib2
import urllib
import re
import httplib
import json
#import cloudstorage as gcs
from datetime import datetime, timedelta
from google.appengine.api import app_identity
from google.appengine.ext import db
from google.appengine.api import users
from google.appengine.ext import blobstore
from google.appengine.ext import ndb
from google.appengine.ext.webapp import blobstore_handlers

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

#this probably needs to change to get the bucket to work
"""
def file_handle(self):
  bucket_name = os.environ.get('BUCKET_NAME', app_identity.get_default_gcs_bucket_name())
  #self.response.headers['Content-Type'] = 'text/plain'
  logging.info('Demo GCS Application running from Version: ' + os.environ['CURRENT_VERSION_ID'] + '\n')
  logging.info('Using bucket name: ' + bucket_name + '\n\n')
  #self.response.write('Demo GCS Application running from Version: ' + os.environ['CURRENT_VERSION_ID'] + '\n')
  #self.response.write('Using bucket name: ' + bucket_name + '\n\n')
"""

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
  upload_url = blobstore.create_upload_url('/upload')
  self.render("newitem.html", upload_url=upload_url)

 def post(self):
  logging.info("******** New Item POST *******")
  upload_url = blobstore.create_upload_url('/upload')
  title = self.request.get("title")
  desc = self.request.get("description")
  location = self.request.get("location")
  if(title==""):
    logging.info("error, submitted blank title")
    error="*Please Add a Title*"
    self.render("newitem.html", error=error, descData=desc, locData=location, upload_url=upload_url)

  else:
    logging.info("no errors, posting item")
    it = Item(title=title, description=desc, location=location)
    it.put()
    #item_id = it.key().id()
    time.sleep(0.1)
    self.redirect('/')

"""
class UploadHandler(Handler):
  def get(self):
    logging.info("enter uploader GET (shouldn't happen)")

  def post(self):
    logging.info("enter uploader POST")
    try:
      upload = self.get_uploads()[0]
      user_photo = UserPhoto(
          user=users.get_current_user().user_id(),
          blob_key=upload.key())
      user_photo.put()
      self.redirect('/')
    except:
      logging.info("ya done goofed boi YAYAYYAYA")
      self.error(500)
"""
 
class PermItem(Handler):
  def get(self, item_id):
    logging.info("entering the permalink for each lost item")
    logging.info("id: "+str(item_id))
    id_int = int(item_id)
    item = Item.get_by_id(id_int)
    logging.info(str(item))
    self.render("item.html", item=item)

  def post(self, item_id):
    id_int = int(item_id)
    item = Item.get_by_id(id_int)
    logging.info("this is if they want to claim an item")
    logging.info(self.request.POST)
    con = httplib.HTTPSConnection("www.google.com")
    con.request("POST", "/recaptcha/api/siteverify", urllib.urlencode({"secret": "6LdVQTQUAAAAAEla2hBTZfXSiBOiaGUjYPVcbzIg", "response": self.request.get("g-recaptcha-response"), "remoteip": self.request.remote_addr}), {"Content-Type": "application/x-www-form-urlencoded"})
    response = con.getresponse()
    data = response.read()
    success = json.loads(data)['success']
    if success:
      item.key.delete()
      time.sleep(0.1)
      self.redirect('/')
    else:
      self.render("item.html", item=item, error="Please complete reCaptcha")

class About(Handler):
  def get(self):
    logging.info("enter about get")
    self.render("about.html")
    file_handle(self)

application = webapp2.WSGIApplication([
 ('/', Home),
 ('/new', NewItem), 
 ('/about', About),
 #('/upload', UploadHandler),
 (r'/item/(\d+)', PermItem),
 (r'/\S+', Home),#who needs 404 errors?
], debug=True)
