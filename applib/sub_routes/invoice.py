
import os
import subprocess
import pdfkit
import base64
import datetime


from flask import (Blueprint, request, url_for, 
                   render_template, redirect, session, flash)


import email, smtplib, ssl
from email import encoders
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


from jinja2 import Template
from jinja2 import Environment, PackageLoader, FileSystemLoader
import random 


from applib.model import db_session
from applib import model as m 
from applib.forms import CreateInvoiceForm
from applib.lib.helper import get_config 


from flask_login import login_required

# +-------------------------+-------------------------+
# +-------------------------+-------------------------+

mod = Blueprint('invoice', __name__, url_prefix='/admin/invoice')

# +-------------------------+-------------------------+
# +-------------------------+-------------------------+


def comma_separation(amt):
    _len = len(str(amt))
    fmt = '{:' + str(_len) + ',.2f}' 
    return fmt.format(float(amt))

def generate_pdf(_template, args, kwargs):

    env = Environment(loader=FileSystemLoader('applib/templates/'))

    template = env.get_template(_template)
    _template = template.render(posts=args, **kwargs)

    template1 = env.get_template('email_body.html')
    _template1 = template1.render(items=args, **kwargs)

    pdf_output = 'invoice_%d.pdf'%random.randrange(10000)  #when rendering with flask this library requires a co plte directory for the style and image file
    pdfkit.from_string(_template, pdf_output, {'orientation': 'Portrait'})

    message_subject = kwargs['type']+" Generated for "+ kwargs['name'].upper()

    send_email(pdf_output, kwargs['email'], message_subject, _template1)

def send_email(filename, receiver_email, msg_subject, email_body):
    
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

        with open(filename, "rb") as attachment:  # Open PDF file in readable binary mode
            part = MIMEBase("application", "octet-stream")   # Add file as application/octet-stream
            part.set_payload(attachment.read())  # Email client can usually download this automatically as attachment

        encoders.encode_base64(part)  # Encode file in ASCII characters to send by email 

        part.add_header(
            "Content-Disposition",
            "attachment; filename=Invoice.{}".format(datetime.datetime.now().strftime("%Y.%m.%d")),  # Add name/header to attachment part
        )
        
        message.attach(part)  # Add attachment to message 
        
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(smtp_server, port, context=context) as server:
            server.login(sender_email, password)
            server.sendmail(
                sender_email, receiver_email, message.as_string() # convert body and attachment messages to string
                )

def calc_discount(query_disc_type, query_disc_value, query_sub_total):
    
    if query_disc_type == 'fixed':
        return query_disc_value
    elif query_disc_type == 'percent':
        return int(query_disc_value)/100.0 * int(query_sub_total)

    return 0



@mod.route('/')
@login_required
def index():

    posts=[]

    with m.sql_cursor() as db:
        #select query from invoice
        sub = db.query(m.Items.invoice_id, 
                       m.func.sum(m.func.cast(m.Items.amount, 
                                              m.ptype.INTEGER)
                                  ).label("sub_total"),
                       ).group_by(
                            m.Items.invoice_id
                       ).subquery()

        qry = db.query( m.Invoice.inv_id, 
                        m.Invoice.invoice_no, m.Client.email, 
                        m.Client.name, m.Invoice.date_value,                      
                        sub.c.sub_total,
                        sub.c.invoice_id,
                      ).outerjoin(sub, sub.c.invoice_id == m.Invoice.inv_id
                                 ).filter(
                                            m.Invoice.client_id==m.Client.id
                                          ).order_by(
                                                        m.Invoice.inv_id.desc()
                                                     ).all()
                                  
    msg = request.args.get('msg')
    if msg:
        flash(msg)

    return render_template('index.html', value=qry)


@mod.route('/checkout/<int:invoice_id>', methods=['POST', 'GET'])
@login_required
def checkout(invoice_id):

    form = CreateInvoiceForm()
    currency_label = {x[0]: x[1] for x in form.currency.choices}

    with m.sql_cursor() as db:
        
        client_invoice_details = db.query(
                                            m.Invoice.inv_id,
                                            m.Invoice.date_value,
                                            m.Invoice.invoice_no,
                                            m.Invoice.purchase_no,
                                            m.Invoice.disc_value,
                                            m.Invoice.disc_type,
                                            m.Invoice.currency,
                                            m.Client.address,
                                            m.Client.post_addr,
                                            m.Client.name,
                                            m.Client.email,
                                            m.Client.phone,
                                            m.Client.id.label('client_id')
                                        ).join(
                                                m.Client,
                                                m.Client.id == m.Invoice.client_id
                                                ).filter(
                                                    m.Invoice.inv_id == invoice_id
                                                    ).first()


        item_for_amount = db.query(m.Items.id, m.Items.item_desc,
                                   m.Items.qty, m.Items.rate,
                                   m.Items.amount
                                  ).filter_by(invoice_id=invoice_id).all()


        data = {
                    'invoice_no': client_invoice_details.invoice_no,
                    'date_value': datetime.datetime.now().strftime("%Y-%m-%d"),
                    'invoice_due': datetime.datetime.now().strftime("%Y-%m-%d"),
                    'purchase_order_no': client_invoice_details.purchase_no,
                    'discount_applied': client_invoice_details.disc_value,
                    'address': client_invoice_details.address,
                    'post_addr': client_invoice_details.post_addr,
                    'name': client_invoice_details.name,
                    'disc_type': client_invoice_details.disc_type,
                    'email': client_invoice_details.email,
                    'phone': client_invoice_details.phone,
                    'currency': currency_label[client_invoice_details.currency]
                }

        data['cur_fmt'] = comma_separation


        _amount = 0
        total = 0

        for x in item_for_amount:
            _amount += float(x.amount)

        data['subtotal'] = _amount
        data['discount'] = calc_discount(client_invoice_details.disc_type, 
                                         client_invoice_details.disc_value, _amount)

        total = _amount - float(data['discount'])
        data['total'] = total

        if request.method == 'POST':

            items = []
            for y in item_for_amount:
                items.append({
                                'id': y.id, 'item_desc': y.item_desc,
                                'qty': y.qty, 'rate': y.rate, 'amount': y.amount
                              })

            # this needs to be replaced to an email template 
            # data['body'] = "Please see the invoice attached in mail."
            data['type'] = "Invoice"
            generate_pdf(_template='new_invoice.html', args=items, kwargs=data)
            
            msg = "Invoice has been emailed to the customer successfully."
            return redirect(url_for('invoice.index', msg=msg))


        # render the page on GET 
        return render_template('checkout.html', 
                                invoice_details=client_invoice_details,
                                client_details=client_invoice_details, 
                                kwargs=data,
                                items=item_for_amount)


@mod.route('/add', methods=['POST', 'GET'])
@login_required
def client_invoice():
    
    form = CreateInvoiceForm(request.form)    
    form.client_id.choices = [(0, 'Select a User...')] 

    with m.sql_cursor() as db:
        qry = db.query(m.Client).order_by(m.Client.id.desc()).all()              
        form.client_id.choices.extend([(g.id, g.name) for g in qry])

        if request.method == 'POST' and form.validate():
     
            # with m.sql_cursor() as db:
            invoice = m.Invoice()
            m.form2model(form, invoice)
            invoice.date_value = datetime.datetime.now()
            invoice.invoice_due = datetime.datetime.now()
            db.add(invoice)
            db.flush()
            invoice.invoice_no = 'INV-%d' %invoice.inv_id
            invoice.purchase_no = invoice.inv_id

            return redirect(url_for('item.add_item', invoice_id=invoice.inv_id))

    return render_template('client_invoice.html', form=form)


@mod.route('/receipt/<int:invoice_id>', methods=['POST', 'GET'])
@login_required
def receipt(invoice_id):

    with m.sql_cursor() as db:

        client_invoice_details = db.query(
                                            m.Invoice.inv_id,
                                            m.Invoice.date_value,
                                            m.Invoice.invoice_no,
                                            m.Invoice.purchase_no,
                                            m.Invoice.disc_value,
                                            m.Invoice.disc_type,
                                            m.Invoice.currency,
                                            m.Client.address,
                                            m.Client.post_addr,
                                            m.Client.name,
                                            m.Client.email,
                                            m.Client.phone
                                        ).join(
                                                m.Client,
                                                m.Client.id == m.Invoice.client_id
                                                ).filter(
                                                    m.Invoice.inv_id == invoice_id
                                                    ).first()


        item_for_amount = db.query(m.Items.id, m.Items.item_desc,
                                   m.Items.qty, m.Items.rate,
                                   m.Items.amount
                                  ).filter_by(invoice_id=invoice_id).all()


        data = {
                    'invoice_no': client_invoice_details.invoice_no,
                    'date_value': datetime.datetime.now().strftime("%Y-%m-%d"),
                    'invoice_due': datetime.datetime.now().strftime("%Y-%m-%d"),
                    'purchase_order_no': client_invoice_details.purchase_no,
                    'discount_applied': client_invoice_details.disc_value,
                    'address': client_invoice_details.address,
                    'post_addr': client_invoice_details.post_addr,
                    'name': client_invoice_details.name,
                    'disc_type': client_invoice_details.disc_type,
                    'email': client_invoice_details.email,
                    'phone': client_invoice_details.phone,
                    'currency': client_invoice_details.currency
                }

        data['cur_fmt'] = comma_separation


        param = {'invoice_id': invoice_id}

        item_for_amount = db.query(
                                    m.Items.id,
                                    m.Items.item_desc,
                                    m.Items.qty,
                                    m.Items.rate,
                                    m.Items.amount
                                ).filter_by(**param).all()

        items = []
        for y in item_for_amount:
            items.append({
                            'id': y.id, 'item_desc': y.item_desc,
                            'qty': y.qty, 'rate': y.rate, 'amount': y.amount
                        })

        _amount = 0.00
        for x in item_for_amount:
            _amount += float(x.amount)

        data['subtotal'] = _amount
        data['discount'] = calc_discount(client_invoice_details.disc_type,
                            client_invoice_details.disc_value, _amount
                            )

        if request.method == 'GET':
            return generate_pdf(_template='new_invoice.html', 
                                args=items, kwargs=data)
