
from flask import (Blueprint, request, url_for, 
				   render_template, redirect, session, flash)

import applib.model as m
from applib.forms import PaymentForm
from applib.lib import helper as h 
from flask_login import login_required
import datetime 


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
	# form.invoice_id.choices = [(0, "Select a User...")]
	
	with m.sql_cursor() as db:
		# qry = db.query(m.Client).order_by(m.Client.id.desc()).all()     
		# form.invoice_id.choices.extend([(g.id, g.name) for g in qry])
		# import pudb
		# pudb.set_trace()

		if request.method == 'POST' and form.validate():
			pay_md = m.Payment()
			m.form2model(form, pay_md)
			pay_md.invoice_id = invoice_id
			# pay_md.name = invoice_name
			pay_md.date_created = datetime.datetime.now()
			db.add(pay_md)
			# db.flush()

			msg = "Payment has being Added"
			return redirect(url_for('payment.index', msg=msg))

	return render_template('add_payment.html', 
						   form=form, 
						   title="Add Payment")
	


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

