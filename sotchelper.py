import os
import webapp2
import jinja2

from google.appengine.ext import db

from roller import roll_four
from validation import *
from users import User

# the location of the html templates
template_dir = os.path.join(os.path.dirname(__file__), 'templates')

# set the jinja environment to the template directory
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir),
								autoescape = True)
								
class Handler(webapp2.RequestHandler):
	"""This class provides page rendering services."""
	
	def write(self, *a, **kw):
		"""Write an arbitrary number of values to the screen. *a will
		contain the template, and **kw will contain the parameters."""
		
		self.response.out.write(*a, **kw)
		
	def render_str(self, template, **params):
		"""Get the template, and insert the parameters."""
		
		t = jinja_env.get_template(template)
		return t.render(params)
		
	def render(self, template, **kw):
		"""Write the template with parameters to the screen, using the
		render_str method."""
		
		self.write(self.render_str(template, **kw))
		
class MainPage(Handler):
	"""This class renders the main page."""
	
	def get(self):
		username = self.request.cookies.get('user_id')
		if username:
			self.render('main.html', message="Welcome, %s" % username)
		else:
			self.render('main.html', message="Welcome, please log in.")
		
class Roller(Handler):
	"""This class describes the helper app of the application,
	which saves stress boxes and consequences, and simulates a
	roll of the Fate dice."""
	
	def get_checkbox_status(self):
		"""Get the status of the checkboxes, and return dict of results."""
		
		# the status of the checkboxes after a roll are kept here
		checked = {"h1c":"", "h2c":"", "h3c":"", "h4c":"", "h5c":"", "h6c":"", "h7c":"", "h8c":"", "h9c":"",
					"c1c":"", "c2c":"", "c3c":"", "c4c":"", "c5c":"", "c6c":"", "c7c":"", "c8c":"", "c9c":""}
		
		# get the status of each checkbox, and store it to maintain
		for i in range(0,10):
			h_box = "h%i" % i
			c_box = "c%i" % i
			h_val = self.request.get(h_box)
			c_val = self.request.get(c_box)
			h_box += "c"
			c_box += "c"
			checked[h_box] = h_val
			checked[c_box] = c_val
			
		return checked
		
	def get_cons_status(self):
		"""Get the current consequences, and return them as a dict."""
		
		cons_dict = {"mild":"", "moderate":"", "severe":""}
		
		cons_dict["mild"] = self.request.get("mild")
		cons_dict["moderate"] = self.request.get("moderate")
		cons_dict["severe"] = self.request.get("severe")
		
		return cons_dict
	
	def get(self):
		"""Render the page when user arrives."""
		
		self.render("helper.html", sign = "  ", fp = "10")
		
	# handles a die roll
	def post(self):
		"""Roll four Fate dice, and maintain state of checkboxes and
		consequences."""
		
		checks = self.get_checkbox_status()
		cons = self.get_cons_status()
		fp = self.request.get("fp")
		status = dict(checks.items() + cons.items())
		status['fp'] = fp
		
		# roll the dice!
		roll = roll_four()
		
		# put a plus sign in front of positive rolls
		if roll>=0:
			roll = "+%i" % roll
			
		# render the page with the roll value, consequences, and checkbox states
		self.render("helper.html", roll=roll, **status)
		
class Register(Handler):
	"""This class handles the registration page of the site."""
	
	def get(self):
		self.render('register.html')
		
	def post(self):
		"""Check if the username is already taken. If not create a new user."""
		
		users = db.GqlQuery("select * from User order by created desc")
		username = self.request.get('username')
		password = self.request.get('password')
		verify = self.request.get('verify')
		
		have_error = False
		error_msg = ""
		
		# check if all values are valid input, and passwords match
		if not valid_username(username):
			error_msg = "Username must be between 3 and 20 alphanumeric characters."
			have_error = True
		else:
			for user in users:
				if user.username == username:
					error_msg = "Username is already in use."
					have_error = True
					
		if not valid_password:
			error_msg = "Password must be between 3 and 20 characters."
			have_error = True
			
		if not password == verify:
			error_msg = "Passwords do not match."
			have_error = True
			
		# if something is invalid, render page again with error message
		if have_error:
			self.render('register.html', username=username, error_msg=error_msg)
		else:
			#otherwise, create a new user, and redirect to main page
			user = User(username=username, password=password)
			user.put()
			username = str(username)
			
			self.response.headers.add_header('Set-Cookie', 'user_id=%s; Path=/' % username)
			self.redirect('/')

app = webapp2.WSGIApplication([('/roller', Roller),
								('/register', Register),
								('/', MainPage)], debug = True)
