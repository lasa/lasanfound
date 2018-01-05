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
import imghdr
from datetime import datetime, timedelta
from google.appengine.api import app_identity
from google.appengine.ext import db
from google.appengine.api import users
from google.appengine.ext import blobstore
from google.appengine.ext import ndb
from google.appengine.ext.webapp import blobstore_handlers
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
import smtplib

#see http://jinja.pocoo.org/docs/api/#autoescaping
def guess_autoescape(template_name):
 if template_name is None or '.' not in template_name:
  return False
  ext = template_name.rsplit('.', 1)[1]
  return ext in ('xml', 'html', 'htm')

JINJA_ENVIRONMENT = jinja2.Environment(
 autoescape=guess_autoescape, #see http://jinja.pocoo.org/docs/api/#autoxscaping
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

#Model for the item objects
class Item(db.Model):
 title = db.StringProperty()
 description = db.StringProperty()
 location = db.StringProperty()
 picture = db.BlobProperty()
 created = db.DateTimeProperty(auto_now_add = True)

class Home(Handler):
 def get(self):
  logging.info("********** WelcomePage GET **********")
  items = db.GqlQuery("SELECT * FROM Item ORDER BY created DESC limit 10")
  self.render("home.html", items=items)

class About(Handler):
  def get(self):
    self.render("about.html")

class NewItem(Handler):
 def get(self):
  logging.info("******** New Item GET ******")
  upload_url = blobstore.create_upload_url('/upload')
  #this needs to include a blob array
  self.render("newitem.html", upload_url=upload_url)

 def post(self):
  #need to add error handling for a file too  large
  logging.info("******** New Item POST *******")
  upload_url = blobstore.create_upload_url('/upload')
  title = cgi.escape(self.request.get("title"), quote=True)
  desc = cgi.escape(self.request.get("description"), quote=True)
  location = cgi.escape(self.request.get("location"), quote=True)
  picture = self.request.get("file")
  img_type = imghdr.what(None, picture)
  img_type = str(img_type)
  supportedtypes = ['png', 'jpeg', 'gif', 'tiff', 'bmp']
  con = httplib.HTTPSConnection("www.google.com")
  con.request("POST", "/recaptcha/api/siteverify", urllib.urlencode({"secret": "6LdVQTQUAAAAAEla2hBTZfXSiBOiaGUjYPVcbzIg", "response": self.request.get("g-recaptcha-response"), "remoteip": self.request.remote_addr}), {"Content-Type": "application/x-www-form-urlencoded"})
  response = con.getresponse()
  data = response.read()
  success = json.loads(data)['success']
  if success:
    if title=="":
      logging.info("error, submitted blank title")
      titleError="*Please Add a Title*"
      self.render("newitem.html", titleError=titleError, descData=desc, locData=location, upload_url=upload_url)
    elif (img_type not in supportedtypes) and (img_type != "None"):
      logging.info("error, invalid file type: "+img_type)
      fileError="*Not Supported Filetype*<br><br>Supported Types: " + ", ".join(supportedtypes)
      self.render("newitem.html", fileError=fileError, descData=desc, locData=location, upload_url=upload_url, titleData=title)
    else:
      logging.info("no errors, posting item")
      if img_type!="None":
        it = Item(title=title, description=desc, location=location, picture=db.Blob(picture))
      else:
        it = Item(title=title, description=desc, Location=location)
      it.put()
      time.sleep(0.1)
      self.redirect('/')
  else:
    self.render("newitem.html", descData=data, locData=location, upload_url=upload_url, )

class PermItem(Handler):
  def get(self, item_id):
    logging.info("entering the permalink for each lost item")
    logging.info("id: "+str(item_id))
    id_int = int(item_id)
    item = Item.get_by_id(id_int)
    self.render("item.html", item=item)

  def post(self, item_id):
    id_int = int(item_id)
    item = Item.get_by_id(id_int)
    logging.info("item: "+str(item.key()))
    logging.info("this is if they want to claim an item")
    con = httplib.HTTPSConnection("www.google.com")
    con.request("POST", "/recaptcha/api/siteverify", urllib.urlencode({"secret": "6LdVQTQUAAAAAEla2hBTZfXSiBOiaGUjYPVcbzIg", "response": self.request.get("g-recaptcha-response"), "remoteip": self.request.remote_addr}), {"Content-Type": "application/x-www-form-urlencoded"})
    response = con.getresponse()
    data = response.read()
    success = json.loads(data)['success']
    if success:
      item.delete()
      logging.info("key: "+str(item))
      time.sleep(0.1)
      self.redirect('/')
    else:
      self.render("item.html", item=item, error="Please complete reCaptcha")

class ImgHandler(Handler):
  def get(self, img_id):
    logging.info("img handler get")
    item = Item.get_by_id(int(img_id))
    if item.picture:
      logging.info(item.title)
      self.response.headers['Content-Type']="image"
      self.response.out.write(item.picture)
    else:
      self.error(404)

class ErrorHandler(Handler):
  def get(self):
    self.render("error.html", error="404 page not found")


application = webapp2.WSGIApplication([
 ('/', Home),
 ('/new', NewItem), 
 ('/about', About),
 (r'/img/(\d+)', ImgHandler),
 (r'/item/(\d+)', PermItem),
 ('/.*', ErrorHandler),#who needs 404 errors?
], debug=True)