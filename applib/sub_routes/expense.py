
from flask import (Blueprint, request, url_for, 
                   render_template, redirect, session, flash)


import applib.model as m
from applib.forms import ExpenseForm
from applib.lib import helper as h 
from flask_login import login_required
import datetime 


mod = Blueprint('expense', __name__, url_prefix='/admin/expense')


@mod.route("/")
@login_required
def index():

    qry = None
    form = ExpenseForm(request.form)
    status = { x[0]: x[1] for x in form.status.choices}

    with m.sql_cursor() as db:
        qry = db.query(m.Expense.id, m.Expense.title,
                m.Expense.desc, m.Expense.date_created, m.Expense.requested_by,
                m.Expense.status, m.Expense.aproved_by
                ).order_by(m.Expense.id.desc()).limit(10).all()
   
    if request.args.get("msg"):
        flash(request.args.get("msg"))

    return render_template("expense.html", data=qry, status_label=status, 
                            date_format=h.date_format)


@mod.route("/add", methods=["GET", "POST"])
def add():

    qry = None
    form = ExpenseForm(request.form)

    if request.method == 'POST' and form.validate():
        
        with m.sql_cursor() as db:                       
            exp_md = m.Expense()
            m.form2model(form, exp_md)
            exp_md.date_created = datetime.datetime.now()
            db.add(exp_md)

        return redirect(url_for("expense.index", 
                        msg="new Expense added, waiting for approval."))

    return render_template("add_expense.html", form=form)



@mod.route("/edit/<int:exp_id>", methods=['GET', 'POST'])
def edit(exp_id):

    form = ExpenseForm(request.form)

    if request.method == 'POST' and form.validate():
        with m.sql_cursor() as db:
            exp_md = db.query(m.Expense).get(exp_id)
            m.form2model(form, exp_md)
        
        return redirect(url_for("expense.index", msg='Expense updated successfully.'))
            
    with m.sql_cursor() as db:
        exp_data = db.query(m.Expense).filter_by(id=exp_id).first()
        m.model2form(exp_data, form)

    return render_template("add_expense.html", title="Edit Expense", form=form)






