
from configobj import ConfigObj

from passlib.hash import pbkdf2_sha256

from flask import session, url_for 
import datetime
import urllib 
import base64

import os
import subprocess
import pdfkit
import base64

# +-------------------------+-------------------------+
# +-------------------------+-------------------------+


def get_config(header, key=None, filename='config.ini'):

	cfg = ConfigObj(filename)
	if not key:
		return cfg[header]

	return cfg[header][key]


# +-------------------------+-------------------------+
# +-------------------------+-------------------------+


class SetUri:
	"""
		# default uri 
		# dialect+driver://username:password@host:port/database

		# default uri 
		# dialect+driver://username:password@host:port/database

		# postgresql uri structure 
		>>> postgresql://scott:tiger@localhost:5432/mydatabase 
		# sqlite uri structure 
		>>> sqlite:///foo.db

	"""

	def __init__(self, db_cfg):
		self.db_cfg = db_cfg


	def set_credentials(self):
		tmp = self.db_cfg
		output = ''
		
		if tmp['username']:
			output = tmp['username'] + ':' + tmp["password"]

		return output


	def set_connections(self):
		
		output = ''

		if self.db_cfg['host']:
			output = '@'+ self.db_cfg['host'] + ':' + self.db_cfg['port']

		return output


	def set_db(self):        
		return  '/' + self.db_cfg['database']


	def set_driver(self):
		output = self.db_cfg['dialect'] 
		if self.db_cfg.get('driver', None):
			output += '+' + self.db_cfg['driver']

		output += '://'

		return output


	def run(self):
		
		return (self.set_driver() + self.set_credentials() 
				+ self.set_connections() + self.set_db()
				)



def set_db_uri():

	_db_cfg = get_config('db')
	uri = SetUri(_db_cfg)
	return uri.run()

# +-------------------------+-------------------------+
# +-------------------------+-------------------------+


def encrypt_passwd(passwd):
	return pbkdf2_sha256.hash(passwd)


def validate_hash(passwd, hash):
	if not passwd or not hash:
		return False

	return pbkdf2_sha256.verify(passwd.encode('utf-8'), hash.encode('utf-8'))

# +-------------------------+-------------------------+
# set and delete session 
# +-------------------------+-------------------------+

# def set_session(site, name, val):
#     session['%s_%d'%(name, site)] = val


# def del_session(site, name):
#     del session['%s_%d'%(name, site)]

# def get_session(site, name):
#     return session['%s_%d'%(name, site)]

# +-------------------------+-------------------------+
# +-------------------------+-------------------------+


def date_format(date_obj, strft='%H: %M: %S'):
	
	now = datetime.datetime.now()
	diff = now - date_obj

	if diff.days == 0:
		retv = date_obj.strftime(strft)

	elif diff.days == 1:
		retv = 'Yesterday'

	elif diff.days > 1 and diff.days < 10:
		retv = date_obj.strftime('%d, %B')

	else:
		retv = date_obj.strftime("%d-%m-%Y")
	

	return retv


def encode_param(**kwargs):        
	tmp = urllib.parse.urlencode(kwargs)
	params = base64.b64encode(tmp.encode('utf-8')).decode('utf-8')

	return params


def decode_param(value): 

	if isinstance(value, str):
		value = value.encode("utf-8")

	ret_val = base64.b64decode(value)
	ret_val = ret_val.decode("utf-8")

	out = {} 

	for x in ret_val.split("&"):
		key,val = x.split("=")
		out[key] = urllib.parse.unquote(val) 

	return out


import email, smtplib, ssl
from email import encoders
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


def send_email(filename, receiver_email, msg_subject, 
			   email_body, email_filename):
	
	email_params = get_config('email')

	if email_params['live'] == '1':

		body = email_body
		port = email_params['ssl']
		smtp_server =  email_params['smtp']
		password = email_params['passwd']
		sender_email = email_params['sender']
		message = MIMEMultipart()
		message["Subject"] = msg_subject
		message["From"] = email_params['sender']
		message["To"] = receiver_email

		message.attach(MIMEText(body, "html"))  #Add body to Email
		# filename = pdf_output  # In same directory as script

		if filename:

			with open(filename, "rb") as attachment:  # Open PDF file in readable binary mode
				part = MIMEBase("application", "octet-stream")   # Add file as application/octet-stream
				part.set_payload(attachment.read())  # Email client can usually download this automatically as attachment

			encoders.encode_base64(part)  # Encode file in ASCII characters to send by email 

			part.add_header(
				"Content-Disposition",
				"attachment; filename={}.{}".format(email_filename, 
													datetime.datetime.now().strftime("%b.%m.%Y.%S"))
			)
			
			message.attach(part)   
		
		context = ssl.create_default_context()
		with smtplib.SMTP_SSL(smtp_server, port, context=context) as server:
			server.login(sender_email, password)
			server.sendmail(
				sender_email, receiver_email, message.as_string()
				)


def set_email_read_feedback(**kwargs):

	variables = encode_param(**kwargs)
	link = url_for("admin.report_email_receipt", 
			ref=variables, 
			_external=True)
	return link


def calc_discount(query_disc_type, query_disc_value, query_sub_total):
	
	if query_disc_type == 'fixed':
		return query_disc_value
	elif query_disc_type == 'percent':
		return int(query_disc_value)/100.0 * int(query_sub_total)

	return 0




from jinja2 import Template
from jinja2 import Environment, PackageLoader, FileSystemLoader
import random 



def generate_pdf(_template, args, kwargs, email_body_template):

	env = Environment(loader=FileSystemLoader('applib/templates/'))

	template = env.get_template(_template)
	_template = template.render(posts=args, **kwargs)
	
	pdf_output = '{}_{}.pdf'.format(kwargs['type'], 
									datetime.datetime.now().strftime("%b.%m.%Y.%S"))
	pdfkit.from_string(_template, pdf_output, {'orientation': 'Portrait'})

	message_subject = kwargs['type']+" Generated for "+ kwargs['name'].upper()

	_link = set_email_read_feedback(email_receiver=kwargs['email'], 
									email_title=message_subject)

	template1 = env.get_template(email_body_template)
	_template1 = template1.render(items=args, status_link=_link, **kwargs)

	send_email(pdf_output, kwargs['email'], message_subject, _template1, kwargs['type'])


def comma_separation(amt):
	_len = len(str(amt))
	fmt = '{:' + str(_len) + ',.2f}' 
	return fmt.format(float(amt))


