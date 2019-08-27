
import os
import subprocess
import pdfkit
import base64
import arrow
import datetime

from flask import (Blueprint, request, url_for, 
                   render_template, redirect, session, flash)

from werkzeug.security import check_password_hash, generate_password_hash
# import records


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
from applib.forms import (ItemForm, DiscountFrm, CreateInvoiceForm)
from applib.lib.helper import get_config 

# from applib.main import login_manager

from flask_login import login_user, login_required, logout_user

# +-------------------------+-------------------------+
# +-------------------------+-------------------------+

mod = Blueprint('admin', __name__, url_prefix='/admin')

# +-------------------------+-------------------------+
# +-------------------------+-------------------------+


def generate_pdf(_template, args, kwargs ):

    env = Environment(loader=FileSystemLoader('applib/templates/'))
    template = env.get_template(_template)
    _template = template.render(posts=args, **kwargs)

    pdf_output = 'invoice_%d.pdf'%random.randrange(10000)  #when rendering with flask this library requires a co plte directory for the style and image file
    pdfkit.from_string(_template, pdf_output, {'orientation': 'Portrait'})

    send_email(pdf_output, kwargs['email'], "message subject", kwargs['body'])


def comma_separation(amt):
    _len = len(str(amt))
    fmt = '{:' + str(_len) + ',.2f}' 
    return fmt.format(float(amt))


def send_email(filename, receiver_email, msg_subject, email_body):
    
    email_params = get_config('email')

    if email_params['live'] == '1':

        body = email_body
        port = email_params['ssl']
        smtp_server =  email_params['smtp_server']
        password = email_params['passwd']
        
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
        # return applied

    return 0



@mod.route('/login', methods = ['GET','POST'])
def login():
    
    error = None

    if request.method == 'POST':
        username = request.form['usr_name']
        password = request.form['psd_wrd']

        with m.sql_cursor() as db:
            
            user = db.query(m.Users).filter(m.Users.username == username
                                            ).first()

            if user is None:
                error = 'Incorrect Username/Password'

            elif not check_password_hash(user.password, password):
                error = 'Incorrect Username or Password'
              
            if error is None:                
                session['user_id'] = user.id

                login_user(user)

                return redirect(url_for('admin.index'))

        flash(error)


    return render_template('login.html')
    


@mod.route('/')
@login_required
def index():

    posts=[]

    with m.sql_cursor() as db:
        #select query from invoice
        sub = db.query(m.Items.invoice_id, m.func.sum(m.func.cast(
                                                                    m.Items.amount, m.ptype.INTEGER
                                                                  )
                                                      ).label("sub_total"),
                       ).group_by(
                            m.Items.invoice_id
                       ).subquery()

        qry = db.query(m.Invoice.inv_id, m.Invoice.invoice_no, m.Invoice.email, 
                       m.Invoice.name, m.Invoice.date_value,                      
                       sub.c.sub_total,
                       sub.c.invoice_id,
                      ).outerjoin(sub, sub.c.invoice_id == m.Invoice.inv_id
                                 ).all()
                                 
       
    msg = request.args.get('msg')
    if msg:
        flash(msg)

    return render_template('index.html', value=qry)



@mod.route('/add/item/<int:invoice_id>', methods=['POST', 'GET'])
@login_required
def add_item(invoice_id):

    form = ItemForm(request.form) 

    if request.method == 'POST' and form.validate():

        params={
            'item_desc': request.form['item_desc'],
            'qty': request.form['qty'],
            'rate': request.form['rate'],
            'amount': request.form['amt']
        }

        with m.sql_cursor() as db:

            params['invoice_id'] = invoice_id 

            # insert item query
            item = m.Items(**params)
            db.add(item)
            db.flush()

            return redirect(url_for('admin.index'))


    return render_template('add_item.html', form=form)


@mod.route('/add/discount/<int:invoice_id>', methods=['POST', 'GET'])
@login_required
def add_discount(invoice_id):

    with m.sql_cursor() as db:

        param = {'invoice_id': invoice_id}
 
        # select query with WHERE request
        resp = db.query(
                            m.Items.id,
                            m.Items.item_desc,
                            m.Items.qty,
                            m.Items.rate,
                            m.Items.amount,
                        ).filter_by(**param).all()

        resp_amount = 0

        if not resp:
            msg = "Please add an item to the invoice first."
            return redirect(url_for('admin.index', msg=msg))

        # select query with WHERE request
        output = db.query(
                            m.Invoice.inv_id,
                            m.Invoice.email,
                            m.Invoice.name,
                            m.Invoice.address,
                            m.Invoice.post_addr,
                            m.Invoice.date_value,
                            m.Invoice.invoice_no,
                            m.Invoice.purchase_no,
                            m.Invoice.disc_value,
                            m.Invoice.disc_type,
                            m.Invoice.invoice_no
                      ).filter_by(
                                 inv_id=invoice_id
                                )

        temp_output = output.first()
         
        for x in resp:
            resp_amount += float(x.amount)

        if temp_output.disc_type is None:
            form = DiscountFrm(sub_total=resp_amount)

        else:

            form = DiscountFrm()
            form.discount_type.data = temp_output.disc_type
            form.discount.data = temp_output.disc_value
            form.disc_amt.data = calc_discount(temp_output.disc_type, 
                                               temp_output.disc_value, 
                                               resp_amount)
            form.sub_total.data = resp_amount 
            form.new_total.data = resp_amount - float(form.disc_amt.data)

         
        if request.method == 'POST':
            
            form = DiscountFrm(**request.form)
            
            if form.validate():

                assert resp_amount > 0 , 'total amount is not supposed to be zero amount'

                #sql update query
                output.update({
                            'disc_type' : form.discount_type.data,
                            'disc_value' : form.discount.data,                      
                        })   
                return redirect(url_for('admin.index'))        

        return render_template('disc.html', form=form)


@mod.route('/checkout/<int:invoice_id>', methods=['POST', 'GET'])
@login_required
def checkout(invoice_id):

    with m.sql_cursor() as db:
        invoice_details = db.query(m.Invoice
                                   ).filter_by(inv_id=invoice_id
                                              ).first()
 
        item_for_amount = db.query(m.Items.id, m.Items.item_desc,
                                   m.Items.qty, m.Items.rate,
                                   m.Items.amount
                                  ).filter_by(**{'invoice_id': invoice_id}).all()

        data = {
                'invoice_no': invoice_details.invoice_no,
                'date_value': datetime.datetime.now().strftime("%Y-%m-%d"),
                'invoice_due': datetime.datetime.now().strftime("%Y-%m-%d"),
                'purchase_order_no': invoice_details.purchase_no,
                'discount_applied': invoice_details.disc_value,
                'address': invoice_details.address,
                'post_addr': invoice_details.post_addr,
                'name': invoice_details.name,
                'disc_type': invoice_details.disc_type,
                'email': invoice_details.email,
                'phone': invoice_details.phone,
                'currency': invoice_details.currency
                }

        data['cur_fmt'] = comma_separation

        _amount = 0
        total = 0

        for x in item_for_amount:
            _amount += float(x.amount)

        data['discount'] = calc_discount(invoice_details.disc_type, 
                                         invoice_details.disc_value, _amount)
        
        # data['discount'] = 0
        # if invoice_details.disc_type == 'fixed':
        #     data['discount'] = invoice_details[0].disc_value
        # elif invoice_details.disc_type == 'percent':
        #     applied = int(invoice_details.disc_value)/100.0 * int(_amount)
        #     data['discount'] = applied
        

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
            data['body'] = "Please see the invoice attached in mail."
            generate_pdf(_template='new_invoice.html', args=items, kwargs=data)
            
            msg = "Invoice has been emailed to the customer successfully."
            return redirect(url_for('admin.index', msg=msg))

    
    # render the page on get 

        return render_template('checkout.html', 
                                invoice_details=invoice_details, 
                                kwargs=data,
                                items=item_for_amount)


@mod.route('/create/invoice', methods=['POST', 'GET'])
@login_required
def create_invoice():

    form = CreateInvoiceForm(request.form)

    if request.method == 'POST' and form.validate():

        with m.sql_cursor() as db:

            params = {
                    'name' : form.name.data, 'address' : form.address.data,
                    'phone' : form.phone.data, 'email' : form.email.data,
                    'post_addr' : form.post_addr.data, 'currency' : form.currency.data.upper(),
                    'date_value' : datetime.datetime.now(),
                    'invoice_due' : datetime.datetime.now()
                } 

            invoice = m.Invoice(**params)
            db.add(invoice)
            db.flush()
            invoice.invoice_no = 'INV-%d' %invoice.inv_id 
            invoice.purchase_no = invoice.inv_id 
 
            return redirect(url_for('admin.add_item',invoice_id=invoice.inv_id))    


    return render_template('create_invoice.html', form=form)


@mod.route('/receipt/<int:invoice_id>', methods=['POST', 'GET'])
@login_required
def receipt(invoice_id):

    with m.sql_cursor() as db:

        # select query with WHERE request
        invoice_details = db.query(m.Invoice).filter_by(inv_id=invoice_id
                                                       ).first()

        param = {'invoice_id': invoice_id}

        # select query with WHERE request
        item_for_amount = db.query(
                            m.Items.id,
                            m.Items.item_desc,
                            m.Items.qty,
                            m.Items.rate,
                            m.Items.amount
                        ).filter_by(**param).all()
       
        for y in item_for_amount:
            items = []
            items.append({
                            'id': y.id, 'item_desc': y.item_desc,
                            'qty': y.qty, 'rate': y.rate, 'amount': y.amount
                        })
        
        data = {
            'invoice_no': invoice_details.invoice_no,
            'date_value': datetime.datetime.now().strftime("%x"),
            'invoice_due': datetime.datetime.now().strftime("%x"),
            'purchase_order_no': invoice_details.purchase_no,
            'paid_to_date': invoice_details.paid_to_date,
            'balance': invoice_details.balance,
            'address': invoice_details.address,
            'post_addr': invoice_details.post_addr,
            'name': invoice_details.name,
            'disc_type': invoice_details.disc_type,
            'email': invoice_details.email
        }

        data['cur_fmt'] = comma_separation

        for x in item_for_amount:
            _amount += float(x.amount)

        

        data['discount'] = get_discount(invoice_details.disc_type,
                            invoice_details.disc_value, _amount
                            )

        # if invoice_details.disc_type == 'fixed':
        #     data['discount'] = invoice_details.disc_value
        # elif invoice_details.disc_type == 'percent':
        #     applied = int(invoice_details.disc_value)/100.0 * int(_amount)
        #     data['discount'] = applied

        if request.method == 'GET':
            return generate_pdf(_template='new_invoice.html', 
                                args=items, kwargs=data)



@mod.route('/edit/item/<int:invoice_id>/<int:item_id>', methods=['POST', 'GET'])
@login_required
def edit_item(invoice_id, item_id):

    with m.sql_cursor() as db:
        param = {'id': item_id}
        # select query with WHERE request
        resp = db.query(
                    m.Items.id,
                    m.Items.item_desc,
                    m.Items.qty,
                    m.Items.rate,
                    m.Items.amount,
                ).filter_by(**param)
       

        temp_resp = resp.first()

        form = ItemForm()
        form.item_desc.data = temp_resp.item_desc
        form.qty.data = temp_resp.qty 
        form.amt.data = temp_resp.amount

        if request.method == 'POST':

            form = ItemForm(request.form)

            if form.validate():
         

                resp.update(
                    {
                        'item_desc' : form.item_desc.data,
                        'qty' : form.qty.data,
                         'rate' : form.rate.data,
                        'amount' : form.amt.data                        
                    })
              
                return redirect(url_for('admin.checkout', invoice_id=invoice_id)) 


    return render_template('edit_item.html', form=form)


@mod.route('/delete/item/<int:invoice_id>/<int:item_id>')
@login_required
def delete_item(invoice_id, item_id):

    with m.sql_cursor() as db:
        param = {'id': item_id}

        # delete object query with WHERE request
        db.query(
                    m.Items                     
                ).filter_by(**param).delete()
 

        return redirect(url_for('admin.checkout', invoice_id=invoice_id)) 

# assert
@mod.route('/edit/invoice/<int:invoice_id>', methods=['POST', 'GET'])
@login_required
def edit_invoice(invoice_id):

    with m.sql_cursor() as db:
        param = {'inv_id': invoice_id}

        # select query with WHERE request
        resp = db.query(
                    m.Invoice.inv_id,
                    m.Invoice.email,
                    m.Invoice.name,
                    m.Invoice.phone,
                    m.Invoice.address,
                    m.Invoice.post_addr,
                    m.Invoice.date_value,
                    m.Invoice.invoice_no,
                    m.Invoice.purchase_no,
                    m.Invoice.disc_value,
                    m.Invoice.disc_type,
                    m.Invoice.invoice_no,
                    m.Invoice.currency
              ).filter_by(
                         **param
                        )

        temp_resp = resp.first()

        form = CreateInvoiceForm()
        form.name.data = temp_resp.name
        form.address.data = temp_resp.address
        form.email.data = temp_resp.email 
        form.phone.data = temp_resp.phone
        form.post_addr.data = temp_resp.post_addr
        form.currency.data = temp_resp.currency

        if request.method == 'POST':

            form = CreateInvoiceForm(request.form)

            if form.validate():

                resp.update(
                            {
                                'name' : form.name.data,
                                'address' : form.address.data,
                                'email' : form.email.data,
                                'phone' : form.phone.data,
                                'post_addr' : form.post_addr.data,
                                'currency' : form.currency.data                            
                            })
               

                return redirect(url_for('admin.checkout', invoice_id=invoice_id)) 
                
    return render_template('create_invoice.html', form=form)


@mod.route("/logout")
@login_required
def logout_app():
    logout_user()
    return redirect(url_for('admin.login'))





