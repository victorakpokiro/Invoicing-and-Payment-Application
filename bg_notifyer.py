
import os
import subprocess
import pdfkit
import base64

# from babel.numbers import format_currency
from jinja2 import Template
from jinja2 import Environment, PackageLoader, FileSystemLoader
import random 
# from applib.api import InvoiceApi 
import json, sys

import email, smtplib, ssl
from email import encoders
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

import records
from contextlib import contextmanager
from configobj import ConfigObj
import time
import locale


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

    _db_cfg = ConfigObj('config.ini')['db']
    uri = SetUri(_db_cfg)
    return uri.run()


@contextmanager
def db_session():
    
    con_str = set_db_uri() 
    
    db = records.Database(con_str, echo=True)

    conn = db.get_connection()
    tx = conn.transaction()

    try:
    
        yield conn
        tx.commit()
    
    except Exception as e:
        tx.rollback()
        raise e 
        # log the error here 
    
    finally:
        conn.close()


# +----------------------------+-----------------------+
# +----------------------------+-----------------------+


def notification_handler():

    # while True:
    with db_session() as db:

        email_param = {'status': 0}
        email_sql = "select * from email_queue where status=:status"
        email_qry = db.query(email_sql, **email_param)
        last_id = email_qry.all()[0].reference

        inv_param = {'inv_id': last_id}
        inv_sql = "select * from invoice where inv_id=:inv_id"
        inv_qry = db.query(inv_sql, **inv_param)
        _output = inv_qry.all()

        # import pudb;pudb.set_trace()
        itm_param = {'id':last_id}
        itm_sql = "select * from item where invoice_id =:id"
        itm_qry = db.query(itm_sql, **itm_param)
        posts = itm_qry.as_dict()


        # sub_total = format_currency( _output[0].sub_total, 'NGN', locale='en_US')
        # disc_value = format_currency( _output[0].disc_value, 'NGN', locale='en_US')
        # total = format_currency( _output[0].total, 'NGN', locale='en_US')
        # paid_to_date = format_currency( _output[0].paid_to_date, 'NGN', locale='en_US')
        # balance = format_currency( _output[0].balance, 'NGN', locale='en_US')

        params = {
                    'invoice_no': _output[0].invoice_no,
                    'date_value': _output[0].date_value,
                    'invoice_due': _output[0].invoice_due,
                    'purchase_order_no': _output[0].purch_no,
                    'subtotal': _output[0].sub_total,
                    'discount_applied': _output[0].disc_value,
                    'total': _output[0].total,
                    'paid_to_date': _output[0].paid_to_date,
                    'balance': _output[0].balance,
                    'address': _output[0].address,
                    'post_addr': _output[0].post_addr,
                    'name': _output[0].name,
                    'disc_type': _output[0].disc_type
                }


        params['cur_fmt'] = comma_separation
        template_render(args=posts, kwargs=params)

        email_updt = {'status': 1, 'id': last_id}
        email_sql = "update email_queue set status=:status where id=:id"
        db.query(email_sql, **email_updt)
                

        # print('bg_notifyer suspends for 5 secs')
        # time.sleep(5)
        # print('bg_notifyer resumes...')


     
def comma_separation(amt):
    _len = len(str(amt))
    fmt = '{:' + str(_len) + ',.2f}' 
    return fmt.format(float(amt))    

    # '{:20,.2f}'.format( )




def template_render(args, kwargs):

    env = Environment(loader=FileSystemLoader('templates/'))
    template = env.get_template('new_invoice.html')
    _template = template.render(posts=args, **kwargs)

    pdf_output = 'invoice_%d.pdf'%random.randrange(10000)  #when rendering with flask this library requires a co plte directory for the style and image file
    pdfkit.from_string(_template, pdf_output, {'orientation': 'Portrait'})

    # send_email(pdf_output, "victorakpokiro@gmail.com", 
    #               "favourakpokiro@gmail.com", "message subject")




def send_email(filename, sender_email, receiver_email, msg_subject):
    
    body = "thank you for paying up below is your invoice" 
    port = 465  # For SSL
    smtp_server = "smtp.gmail.com"
    password = input("Type your password and press enter: ")
    
    message = MIMEMultipart()
    message["Subject"] = msg_subject
    message["From"] = sender_email
    message["To"] = receiver_email

    
    message.attach(MIMEText(body, "html"))  #Add body to Email
    # filename = pdf_output  # In same directory as script

    with open(filename, "rb") as attachment:  # Open PDF file in readable binary mode
        part = MIMEBase("application", "octet-stream")   # Add file as application/octet-stream
        part.set_payload(attachment.read())  # Email client can usually download this automatically as attachment

    encoders.encode_base64(part)  # Encode file in ASCII characters to send by email 

    part.add_header(
        "Content-Disposition",
        "attachment; filename= Invoice",  # Add name/header to attachment part
    )

    
    message.attach(part)  # Add attachment to message 
    
    context = ssl.create_default_context()
    with smtplib.SMTP_SSL(smtp_server, port, context=context) as server:
        server.login(sender_email, password)
        server.sendmail(
            sender_email, receiver_email, message.as_string() # convert body and attachment messages to string
            )




if __name__ == '__main__':

    notification_handler()
  







 


  