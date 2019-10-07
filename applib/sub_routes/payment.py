
from flask import (Blueprint, request, url_for, 
				   render_template, redirect, session, flash)

import applib.model as m
from applib.forms import PaymentForm, CreateInvoiceForm
from applib.lib import helper as h 
from applib.lib.helper import (get_config, send_email, calc_discount,
								set_email_read_feedback, generate_pdf, comma_separation)
from flask_login import login_required

import os
import subprocess
import pdfkit
import base64
import datetime

from jinja2 import Template
from jinja2 import Environment, PackageLoader, FileSystemLoader
import random


mod = Blueprint('payment', __name__, url_prefix='/admin/payment')

@mod.route("/")
@login_required
def index():
	form = PaymentForm(request.form)
	status = { x[0]: x[1] for x in form.status.choices}


	with m.sql_cursor() as db:
		qry = db.query(m.Payment.id,
					   m.Payment.payment_desc,
					   m.Payment.date_created,
					   m.Payment.payment_mode,
					   m.Payment.amount_paid,
					   m.Payment.balance,
					   m.Payment.invoice_id,
					   m.Payment.status,
					   m.Client.name,
					   m.Invoice.inv_id.label("inv_id"),
					  ).join(m.Invoice,
							 m.Invoice.inv_id == m.Payment.invoice_id
							 ).join(m.Client,
									m.Client.id == m.Invoice.client_id
									).filter(m.Payment.invoice_id == m.Invoice.inv_id
									).order_by(m.Invoice.inv_id.desc()).limit(10).all()


	msg = request.args.get("msg")
	if msg:
		flash(msg)


	return render_template('payment.html', data=qry, status_label=status,
							date_format=h.date_format)


@mod.route("/add/<int:invoice_id>/<invoice_name>", methods=["POST", "GET"])
@login_required
def add(invoice_name, invoice_id):
	form = PaymentForm(request.form, client_name=invoice_name)
	form_inv = CreateInvoiceForm()
	currency_label = {x[0]: x[1] for x in form_inv.currency.choices} 
	
	with m.sql_cursor() as db:
		item_details = db.query(m.Items.amount, m.Items.item_desc).filter_by(
														invoice_id=invoice_id
														).all()
		invoice_query = db.query( m.Invoice.inv_id,
								  m.Invoice.disc_type, 
								  m.Invoice.disc_value,
								  m.Invoice.currency).filter_by(
																inv_id=invoice_id
																).first()
		data = {}
		total = 0
		_amount = 0
		for x in item_details:
			_amount += float(x.amount) 

		discount = calc_discount(invoice_query.disc_type, 
								 invoice_query.disc_value, _amount)
		
		total = _amount - float(discount)

		data['cur_fmt'] = comma_separation
		data['currency'] = currency_label[invoice_query.currency]    
	

		if request.method == 'POST' and form.validate():
			pay_md = m.Payment()
			m.form2model(form, pay_md)
			pay_md.invoice_id = invoice_id
			pay_md.date_created = datetime.datetime.now().strftime("%b-%m-%d")
			db.add(pay_md)
			# db.flush()

			msg = "Payment has being Added"
			return redirect(url_for('payment.index', msg=msg))

	return render_template('add_payment.html', 
						   form=form, 
						   title="Add Payment",
						   total=total,
						   item_details=item_details,
						   kwargs=data,
						   invoice_query=invoice_query)
	


@mod.route("/edit/<int:pay_id>/<int:invoice_id>", methods=["POST", "GET"])
@login_required
def edit(pay_id, invoice_id):

	form = PaymentForm(request.form)
	form_inv = CreateInvoiceForm()
	currency_label = {x[0]: x[1] for x in form_inv.currency.choices}
	
	if request.method == 'POST' and form.validate():
		with m.sql_cursor() as db:
			pay_md = db.query(m.Payment).get(pay_id)
			m.form2model(form, pay_md)
		
		return redirect(url_for("payment.index", msg='Paymemt updated successfully.'))
			
	with m.sql_cursor() as db:

		item_details = db.query(m.Items.amount, 
								m.Items.item_desc
								).filter_by(
											invoice_id=invoice_id
											).all()

		invoice_query = db.query(m.Invoice.inv_id, m.Invoice.disc_type, 
								 m.Invoice.disc_value,m.Invoice.currency
								 ).filter_by(inv_id=invoice_id).first()
		
		data = {}
		total = 0
		_amount = 0
		for x in item_details:
			_amount += float(x.amount) 

		discount = calc_discount(invoice_query.disc_type, 
								 invoice_query.disc_value, _amount)
		
		total = _amount - float(discount)

		data['cur_fmt'] = comma_separation
		data['currency'] = currency_label[invoice_query.currency]    
		pay_data = db.query(m.Payment.id,
							m.Client.name.label('client_name'),
							m.Payment.payment_desc,
							m.Payment.client_name,
							m.Payment.payment_mode,
							m.Payment.amount_paid,
							m.Payment.balance,
							m.Payment.status
							).join(
							m.Invoice,
							m.Invoice.inv_id == m.Payment.invoice_id
							).join(
							m.Client, m.Client.id == m.Invoice.client_id
							).filter(m.Payment.id == pay_id).first()

		m.model2form(pay_data, form)

	return render_template("add_payment.html", 
							form=form, 
							title="Edit Payment",
							total=total,
							item_details=item_details,
							kwargs=data,
							invoice_query=invoice_query)


@mod.route("/receipt/<int:invoice_id>", methods=['POST', 'GET'])
@login_required
def receipt(invoice_id):

	form_pay = PaymentForm()
	status = {x[0]: x[1] for x in form_pay.status.choices}

	form_inv = CreateInvoiceForm()
	currency_label = {x[0]: x[1] for x in form_inv.currency.choices}

	with m.sql_cursor() as db:
		client_invoice_details = db.query(m.Invoice.inv_id.label("invoice_id"),
										  m.Invoice.invoice_no, m.Invoice.disc_value,
										  m.Invoice.disc_type, m.Invoice.currency,
										  m.Payment.amount_paid, m.Payment.status, 
										  m.Payment.date_created,
										  m.Payment.balance, m.Client.address,
										  m.Client.post_addr, m.Client.name,
										  m.Client.email, m.Client.phone
										).join(m.Invoice,
							 				   m.Invoice.inv_id == m.Payment.invoice_id
							 			).join(m.Client,
											   m.Client.id == m.Invoice.client_id
											   ).filter(
											   		m.Payment.invoice_id == invoice_id
													).first()

		data = {
				'invoice_no': client_invoice_details.invoice_no,
				'date_value': client_invoice_details.date_created,
				'address': client_invoice_details.address,
				'post_addr': client_invoice_details.post_addr,
				'name': client_invoice_details.name,
				'email': client_invoice_details.email,
				'phone': client_invoice_details.phone
			}

		data['cur_fmt'] = comma_separation

		item_for_amount = db.query(
									m.Items.id,
									m.Items.item_desc,
									m.Items.qty,
									m.Items.rate,
									m.Items.amount
								).filter_by(invoice_id=invoice_id).all()

		items = []
		for y in item_for_amount:
			items.append({
							'id': y.id, 'item_desc': y.item_desc,
							'qty': y.qty, 'rate': y.rate, 'amount': y.amount
						})
		total = 0.00
		_amount = 0.00
		
		for x in item_for_amount:
			_amount += float(x.amount)

		data['type'] = "Receipt"
		data['amount_balance'] = client_invoice_details.balance
		data['amount_paid'] = client_invoice_details.amount_paid
		data['discount'] = calc_discount(client_invoice_details.disc_type,
							client_invoice_details.disc_value, _amount
							)
		total = _amount - float(data['discount'])
		data['total'] = total
		data['status'] = status[client_invoice_details.status]
		data['currency'] = currency_label[client_invoice_details.currency]

		if request.method == 'GET':
			generate_pdf(_template='receipt.html', args=items, 
						 kwargs=data, email_body_template='email_receipt.html')
			
			msg = "Receipt has been emailed to the Customer successfully."
			return redirect(url_for('payment.index', msg=msg))



