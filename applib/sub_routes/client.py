
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
from applib.lib.helper import get_config 

# from applib.main import login_manager

from flask_login import login_required

# +-------------------------+-------------------------+
# +-------------------------+-------------------------+

mod = Blueprint('client', __name__, url_prefix='/admin/client')



@mod.route('/create/client', methods=['POST', 'GET'])
@login_required
def create_client():

    form = CreateClientForm(request.form)

    if request.method == 'POST' and form.validate():

        with m.sql_cursor() as db:

            client_params = {
                    'name' : form.name.data, 'address' : form.address.data,
                    'phone' : form.phone.data, 'email' : form.email.data,
                    'post_addr' : form.post_addr.data, 
                }

            client = m.Client(**client_params)
            db.add(client)
            db.flush()
          
            return redirect(url_for('invoice.client_invoice'))    


    return render_template('create_client.html', form=form)

@mod.route('/invoice/<int:invoice_id>', methods=['POST', 'GET'])
@login_required
def edit_client(invoice_id):

    with m.sql_cursor() as db:
        param = {'id': invoice_id}

        # select query with WHERE request
        resp = db.query(
                            m.Client.email,
                            m.Client.name,
                            m.Client.phone,
                            m.Client.address,
                            m.Client.post_addr
                        ).filter_by(**param)

        temp_resp = resp.first()

        form = CreateClientForm()
        form.name.data = temp_resp.name
        form.address.data = temp_resp.address
        form.email.data = temp_resp.email 
        form.phone.data = temp_resp.phone
        form.post_addr.data = temp_resp.post_addr

        if request.method == 'POST':

            form = CreateClientForm(request.form)

            if form.validate():

                resp.update(
                            {
                                'name' : form.name.data,
                                'address' : form.address.data,
                                'email' : form.email.data,
                                'phone' : form.phone.data,
                                'post_addr' : form.post_addr.data                           
                            })
               

                return redirect(url_for('invoice.checkout', invoice_id=invoice_id)) 
                
    return render_template('create_client.html', form=form)

