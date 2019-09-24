
from flask import (Blueprint, request, url_for, 
				   render_template, redirect, session, flash)

import applib.model as m
from applib.forms import PaymentForm, CreateInvoiceForm
from applib.lib import helper as h 
from flask_login import login_required
import datetime 


mod = Blueprint('payment', __name__, url_prefix='/admin/payment')


def calc_discount(query_disc_type, query_disc_value, query_sub_total):
	
	if query_disc_type == 'fixed':
		return query_disc_value
	elif query_disc_type == 'percent':
		return int(query_disc_value)/100.0 * int(query_sub_total)

	return 0


def comma_separation(amt):
	_len = len(str(amt))
	fmt = '{:' + str(_len) + ',.2f}' 
	return fmt.format(float(amt))



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
					   m.Payment.invoice_id,
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
	formd = CreateInvoiceForm()
	currency_label = {x[0]: x[1] for x in formd.currency.choices} 
	
	with m.sql_cursor() as db:
		item_details = db.query(m.Items.amount, m.Items.item_desc).filter_by(
														invoice_id=invoice_id
														).all()
		discount_query = db.query(m.Invoice.disc_type, 
								  m.Invoice.disc_value,
								  m.Invoice.currency).filter_by(
																inv_id=invoice_id
																).first()

		data = {}
		
		total = 0
		_amount = 0
		for x in item_details:
			_amount += float(x.amount) 

		discount = calc_discount(discount_query.disc_type, 
								 discount_query.disc_value, _amount)
		
		total = _amount - float(discount)

		data['cur_fmt'] = comma_separation
		data['currency'] = currency_label[discount_query.currency]    
	

		if request.method == 'POST' and form.validate():
			pay_md = m.Payment()
			m.form2model(form, pay_md)
			pay_md.invoice_id = invoice_id
			pay_md.date_created = datetime.datetime.now()
			db.add(pay_md)
			# db.flush()

			msg = "Payment has being Added"
			return redirect(url_for('payment.index', msg=msg))

	return render_template('add_payment.html', 
						   form=form, 
						   title="Add Payment",
						   total=total,
						   item_details=item_details,
						   kwargs=data)
	


@mod.route("/edit/<int:pay_id>", methods=["POST", "GET"])
@login_required
def edit(pay_id):

	form = PaymentForm(request.form)
	
	if request.method == 'POST' and form.validate():
		with m.sql_cursor() as db:
			pay_md = db.query(m.Payment).get(pay_id)
			m.form2model(form, pay_md)
		
		return redirect(url_for("payment.index", msg='Paymemt updated successfully.'))
			
	with m.sql_cursor() as db:
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
							form=form, title="Edit Payment")

