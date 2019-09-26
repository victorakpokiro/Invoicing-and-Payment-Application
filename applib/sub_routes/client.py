
import os
import subprocess
import pdfkit
import base64
import datetime

from flask import (Blueprint, request, url_for, 
                   render_template, redirect, session, flash)


from applib.model import db_session
from applib import model as m 
from applib.forms import CreateClientForm
from applib.lib.helper import get_config, date_format

# from applib.main import login_manager

from flask_login import login_required

# +-------------------------+-------------------------+
# +-------------------------+-------------------------+

mod = Blueprint('client', __name__, url_prefix='/admin/client')


@mod.route('/add', methods=['POST', 'GET'])
@login_required
def create_client():

    form = CreateClientForm(request.form)

    if request.method == 'POST' and form.validate():

        with m.sql_cursor() as db:

            client_params = {
                    'name' : form.name.data, 'address' : form.address.data,
                    'phone' : form.phone.data, 'email' : form.email.data,
                    'post_addr' : form.post_addr.data, "date_created": datetime.datetime.now()
                }

            client = m.Client(**client_params)
            db.add(client)
            db.flush()
          
            return redirect(url_for('invoice.client_invoice'))    


    return render_template('create_client.html', form=form)

@mod.route('/edit/<int:client_id>', methods=['POST', 'GET'])
@login_required
def edit_client(client_id):

    form = CreateClientForm(request.form)

    if request.method == 'POST' and form.validate(): 
        
        with m.sql_cursor() as db:
            qry = db.query(m.Client).get(client_id)
            m.form2model(form, qry)
            db.add(qry)

        return redirect(url_for('client.client_list')) 
    

    # when the method is a get 
    with m.sql_cursor() as db:
        qry = db.query(m.Client).get(client_id)
        m.model2form(qry, form)

    return render_template('create_client.html', form=form)



@mod.route("/")
@login_required
def client_list():

    with m.sql_cursor() as db:
        qry = db.query(m.Client.id, m.Client.name,                         
                       m.Client.address, m.Client.email,
                       m.Client.phone, m.Client.date_created
                       ).order_by(m.Client.id.desc()
                                  ).limit(50).all()


    return render_template("client.html", data=qry, date_format=date_format)


