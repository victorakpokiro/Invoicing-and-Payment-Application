
from flask import Blueprint, request, url_for, render_template, redirect, session, flash
from applib.model import db_session
from werkzeug.security import check_password_hash, generate_password_hash
import records
from wtforms import form, validators, fields
from wtforms.form import Form
from wtforms.fields import StringField, SubmitField, DateField, IntegerField, TextAreaField, SelectField
from wtforms.validators import ValidationError, InputRequired, Length, Email

import os
import subprocess
import pdfkit
import base64
import arrow

import email, smtplib, ssl
from email import encoders
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from jinja2 import Template
from jinja2 import Environment, PackageLoader, FileSystemLoader
import random 

mod = Blueprint('admin', __name__, url_prefix='/admin')


def input_required():

    def check_length( form, field ):
        if not field.data:
            raise ValidationError("input is required")

    return check_length


def length( min=3, max=12 ):

    def _length(form, field):

        _field = str(field.data)
        if len(_field) < min:
            raise ValidationError("Length of field must be greater than %d"%min)

        if len(_field) > max:
            raise ValidationError("Length of Field Exceeded")

    return _length

def check_inp_length():

    def validate_amount(form, field):
        try: 
            float(field.data)
        except Exception as e:
            raise ValidationError('Valid Amount or Input Required.')

    return validate_amount


class DiscountFrm(Form):
    discount_type = SelectField('Discount Type :', 
                                choices=[('select', 'Select...'), 
                                         ('fixed', 'Fixed'), 
                                         ('percent', 'Percentage')], 
                                render_kw={"class_": "form-control", 
                                           "style": "margin-bottom : 10px"})

    discount = IntegerField('Discount Applied :', [length(min=1)], 
                            render_kw={"class_": "form-control", 
                                       "autocomplete": "off"})

    disc_amt = IntegerField('Discount Value :', 
                            render_kw={"class_": "form-control", 
                                       "readonly": "readonly"})

    sub_total = IntegerField('Sub-Total :', [check_inp_length()], 
                             render_kw={"class_": "form-control", 
                                        "readonly": "readonly"})

    new_total = IntegerField('New Total :', 
                             render_kw={"class_": "form-control", 
                                     "readonly": "readonly"
                                    })


class CreateInvoiceForm(Form):
    name = StringField('Name :', [InputRequired()], 
                                render_kw={"class_": "form-control", 
                                            "autocomplete": "new-password"})
    address = TextAreaField('Address :', [InputRequired()], 
                                render_kw={"class_": "form-control", 
                                            "autocomplete": "new-password"})
    email = StringField('Email :', [InputRequired(), Email()], 
                                render_kw={"class_": "form-control", 
                                            "autocomplete": "new-password"})
    phone = IntegerField('Phone Number :', [InputRequired(), length(), 
                                                check_inp_length()], 
                                render_kw={"class_": "form-control", 
                                            "autocomplete": "new-password"})
    post_addr = StringField('Postal-Address :', [InputRequired()], 
                                render_kw={"class_": "form-control"})
    currency = StringField('Currency : ', [InputRequired()], 
                                render_kw={"class_": "form-control", 
                                            "autocomplete": "new-password"})

class ItemForm(Form):
    item_desc = TextAreaField('Description :', [InputRequired()], 
                                render_kw={"class_": "form-control", 
                                            "autocomplete": "new-password"})
    qty = IntegerField('Quantity :', [InputRequired()], 
                                render_kw={"class_": "form-control", 
                                            "autocomplete": "new-password"})
    rate = IntegerField('Rate :', [InputRequired()], 
                                render_kw={"class_": "form-control", 
                                            "autocomplete": "new-password"})
    amt = IntegerField('Amount :', 
                                render_kw={"class_": "form-control", 
                                            "readonly": "readonly"})

  


def template_render(_template, args, kwargs ):

    env = Environment(loader=FileSystemLoader('applib/templates/'))
    template = env.get_template(_template)
    _template = template.render(posts=args, **kwargs)

    pdf_output = 'invoice_%d.pdf'%random.randrange(10000)  #when rendering with flask this library requires a co plte directory for the style and image file
    pdfkit.from_string(_template, pdf_output, {'orientation': 'Portrait'})

    send_email(pdf_output, "victorakpokiro@gmail.com", 
                kwargs['email'], "message subject")


def comma_separation(amt):
    _len = len(str(amt))
    fmt = '{:' + str(_len) + ',.2f}' 
    return fmt.format(float(amt))


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


def calc_discount(query_disc_type, query_disc_value, query_sub_total):
    if query_disc_type == 'fixed':
        return query_disc_value
    elif query_disc_type == 'percent':
        applied = int(query_disc_value)/100.0 * int(query_sub_total)
        return applied


@mod.route('/login', methods = ['GET','POST'])
def login():

    error = None

    if request.method == 'POST':
        username = request.form['usr_name']
        password = request.form['psd_wrd']

        with db_session() as db:

            param = {'username': username}
            sql = "select * from users where username=:username"
            user = db.query(sql, **param).first()
  
            if user is None:
                error = 'Incorrect Username/Password'

            elif not check_password_hash(user.password, password):
                error = 'Incorrect Username or Password'
              
            if error is None:
                session.clear()
                session['user_id'] = user['id'] 
                return redirect(url_for('admin.index'))

            flash(error)


    return render_template('login.html')
    


@mod.route('/index')
def index():

    posts=[]

    with db_session() as db:

        sql = "select * from invoice order by inv_id desc"
        qry = db.query(sql)
        posts = qry.as_dict()

    msg = request.args.get('msg')
    if msg:
        flash(msg)

    return render_template('index.html', value=posts)



@mod.route('/add_item/<int:invoice_id>', methods=['POST', 'GET'])
def add_item(invoice_id):

    form = ItemForm(request.form) 

    if request.method == 'POST' and form.validate():

        params={
            'desc': request.form['item_desc'],
            'quant': request.form['qty'],
            'rate': request.form['rate'],
            'amount': request.form['amt']
        }

        with db_session() as db:

            params['invoice_id'] = invoice_id 

            db.query("""
                        insert into item
                        values (
                            nextval('item_sequence'), :desc, :quant, :rate, :amount, :invoice_id
                        )
                    """, **params)

            return redirect(url_for('admin.index'))


    return render_template('add_item.html', form=form)


@mod.route('/add_discount/<int:invoice_id>', methods=['POST', 'GET'])
def add_discount(invoice_id):

    with db_session() as db:

        param = {'id': invoice_id}
        sql =  "select * from item where invoice_id=:id"
        resp = db.query(sql, **param).all()
        
        resp_amount = 0

        if not resp:
            msg = "Please add an item to the invoice first."
            return redirect(url_for('admin.index', msg=msg))

        qry = "select * from invoice where inv_id=:id"
        output = db.query( qry, **param).first() 

        for x in resp:
            resp_amount += float(x.amount)

        if output.disc_type is None:
            form = DiscountFrm(sub_total=resp_amount)

        else:

            form = DiscountFrm()
            form.discount_type.data = output.disc_type
            form.discount.data = output.disc_value
            form.disc_amt.data = calc_discount(output.disc_type, 
                                               output.disc_value, 
                                               resp_amount)
            form.sub_total.data = resp_amount 
            form.new_total.data = resp_amount - float(form.disc_amt.data)

         
        if request.method == 'POST':
            
            form = DiscountFrm(**request.form)
            
            if  form.validate():

                assert resp_amount > 0 , 'total amount is not supposed to be zero amount'

                params = {
                            'disc_type' : form.discount_type.data,
                            'disc_value' : form.discount.data,                      
                         } 

         
                params['id'] = invoice_id

                db.query("""UPDATE invoice
                            SET disc_type=:disc_type, 
                                disc_value=:disc_value
                            WHERE inv_id =:id

                """, **params) 


                return redirect(url_for('admin.index'))        



        return render_template('disc.html', form=form)


@mod.route('/checkout/<int:invoice_id>', methods=['POST', 'GET'])
def checkout(invoice_id):

    invoice_details=[]

    with db_session() as db:

        param = {'id': invoice_id}
        sql = "select * from invoice where inv_id=:id "
        qry = db.query(sql, **param)
        invoice_details = qry.all()

        # params = {'id': invoice_id}
        itm_sql = "select * from item where invoice_id=:id"
        itm_qry = db.query(itm_sql, **param)
        item_for_amount = itm_qry.all()
        items = itm_qry.as_dict()



        data = {
            'invoice_no': invoice_details[0].invoice_no,
            'date_value': arrow.now().format('YYYY-MM-DD'),
            'invoice_due': arrow.now().format('YYYY-MM-DD'),
            'purchase_order_no': invoice_details[0].purchase_no,
            'discount_applied': invoice_details[0].disc_value,
            'address': invoice_details[0].address,
            'post_addr': invoice_details[0].post_addr,
            'name': invoice_details[0].name,
            'disc_type': invoice_details[0].disc_type,
            'email': invoice_details[0].email
        }

        data['cur_fmt'] = comma_separation

        _amount = 0
        total = 0

        for x in item_for_amount:
            _amount += float(x.amount)

        if invoice_details[0].disc_type == 'fixed':
            data['discount'] = invoice_details[0].disc_value
        elif invoice_details[0].disc_type == 'percent':
            applied = int(invoice_details[0].disc_value)/100.0 * int(_amount)
            data['discount'] = applied
        else:
            data['discount'] = 0

        total = _amount - float(data['discount'])
        data['total'] = total

        if request.method == 'POST':
            template_render(_template='new_invoice.html', args=items, kwargs=data)


    return render_template('checkout.html', 
                            invoice_details=invoice_details, 
                            kwargs=data,
                            items=items)


@mod.route('/create_invoice', methods=['POST', 'GET'])
def create_invoice():

    form = CreateInvoiceForm(request.form)

    if request.method=='POST' and form.validate():

        name = request.form['name']
        address = request.form['address']
        phone = request.form['phone']
        email = request.form['email']
        post_addr = request.form['post_addr']
        currency = request.form['currency'].upper()

        with db_session() as db:

            params = {
                    'name' : name,
                    'address' : address,
                    'phone' : phone,
                    'email' : email,
                    'post_addr' : post_addr,
                    'currency' : currency,
                    'date_value' : arrow.now().format('YYYY-MM-DD'),
                    'invoice_due' : arrow.now().format('YYYY-MM-DD'),
                } 


            kent = db.query("select * from invoice_sequence").first()
            
            tmp_val = str(kent.last_value + 1)

            params['invoice_no'] = 'INV-' + tmp_val
            params['purchase_no'] = tmp_val
            
            db.query("""INSERT INTO invoice(inv_id, name, address, 
                                            phone, email, post_addr, 
                                            currency, date_value, invoice_due, 
                                            invoice_no, purchase_no)
                                    VALUES(
                                            nextval('invoice_sequence'), :name, :address, 
                                            :phone, :email, :post_addr, :currency, 
                                            :date_value, :invoice_due, :invoice_no,
                                            :purchase_no
                                          )
                      """, **params)

            return redirect(url_for('admin.add_item',invoice_id=tmp_val))

        


    return render_template('invoice_detail.html', form=form)


@mod.route('/receipt/<int:invoice_id>', methods=['POST', 'GET'])
def receipt(invoice_id):

    invoice_details=[]

    with db_session() as db:

        param = {'id': invoice_id}
        sql = "select * from invoice where inv_id=:id "
        qry = db.query(sql, **param)
        invoice_details = qry.all()


        itm_sql = "select * from item where invoice_id=:id"
        itm_qry = db.query(itm_sql, **param)
        item_for_amount = itm_qry.all()
        items = itm_qry.as_dict()

        
        data = {
            'invoice_no': invoice_details[0].invoice_no,
            'date_value': arrow.now().format('YYYY-MM-DD'),
            'invoice_due': arrow.now().format('YYYY-MM-DD'),
            'purchase_order_no': invoice_details[0].purchase_no,
            # 'subtotal': invoice_details[0].sub_total,
            'discount_applied': invoice_details[0].disc_value,
            # 'total': invoice_details[0].total,
            'paid_to_date': invoice_details[0].paid_to_date,
            'balance': invoice_details[0].balance,
            'address': invoice_details[0].address,
            'post_addr': invoice_details[0].post_addr,
            'name': invoice_details[0].name,
            'disc_type': invoice_details[0].disc_type,
            'email': invoice_details[0].email
        }

        data['cur_fmt'] = comma_separation

        for x in item_for_amount:
            _amount += float(x.amount)

        if invoice_details[0].disc_type == 'fixed':
            data['discount'] = invoice_details[0].disc_value
        elif invoice_details[0].disc_type == 'percent':
            applied = int(invoice_details[0].disc_value)/100.0 * int(_amount)
            data['discount'] = applied

        if request.method == 'GET':
            return template_render(_template='new_invoice.html', args=items, kwargs=data)


@mod.route('/edit_item/<int:invoice_id>/<int:item_id>', methods=['POST', 'GET'])
def edit_item(invoice_id, item_id):

    with db_session() as db:
        param = {'id': item_id}
        sql =  "select * from item where id=:id"
        resp = db.query(sql, **param).first()


        form = ItemForm()
        form.item_desc.data = resp.item_desc
        form.qty.data = resp.qty
        form.rate.data = resp.rate 
        form.amt.data = resp.amount

        if request.method == 'POST':

            form = ItemForm(request.form)

            if form.validate():
                params = {
                            'item_desc' : form.item_desc.data,
                            'qty' : form.qty.data,
                            'rate' : form.rate.data,
                            'amount' : form.amt.data                        
                         } 
                params['id'] = item_id
                db.query("""UPDATE item
                            SET item_desc=:item_desc, 
                                qty=:qty, 
                                rate=:rate,
                                amount=:amount
                            WHERE id =:id

                """, **params) 


                return redirect(url_for('admin.checkout', invoice_id=invoice_id)) 


    return render_template('edit_item.html', form=form)



@mod.route('/delete_item/<int:invoice_id>/<int:item_id>')
def delete_item(invoice_id, item_id):

    with db_session() as db:
        param = {'id': item_id}
        sql =  "DELETE FROM item WHERE id=:id"
        resp = db.query(sql, **param)

        return redirect(url_for('admin.checkout', invoice_id=invoice_id)) 


@mod.route('edit_invoice/<int:invoice_id>', methods=['POST', 'GET'])
def edit_invoice(invoice_id):

    with db_session() as db:
        param = {'id': invoice_id}
        sql =  "select * from invoice where inv_id=:id"
        resp = db.query(sql, **param).first()


        form = CreateInvoiceForm()
        form.name.data = resp.name
        form.address.data = resp.address
        form.email.data = resp.email 
        form.phone.data = resp.phone
        form.post_addr.data = resp.post_addr
        form.currency.data = resp.currency

        if request.method == 'POST':

            form = CreateInvoiceForm(request.form)

            if form.validate():
                params = {
                            'name' : form.name.data,
                            'address' : form.address.data,
                            'email' : form.email.data,
                            'phone' : form.phone.data,
                            'post_addr' : form.post_addr.data,
                            'currency' : form.currency.data                            
                         } 
                params['id'] = invoice_id
                
                db.query("""UPDATE invoice
                            SET name=:name, 
                                address=:address, 
                                email=:email,
                                phone=:phone,
                                post_addr=:post_addr,
                                currency=:currency
                            WHERE inv_id =:id

                """, **params) 


                return redirect(url_for('admin.checkout', invoice_id=invoice_id)) 
                
    return render_template('invoice_detail.html', form=form)






