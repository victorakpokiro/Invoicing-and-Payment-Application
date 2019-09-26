
import os
import subprocess
import datetime

from flask import (Blueprint, request, url_for, 
                   render_template, redirect, session, flash)


from werkzeug.security import check_password_hash, generate_password_hash
from applib.forms import LoginForm

from applib.model import db_session
from applib import model as m 
from applib.lib.helper import get_config, decode_param, send_email

# from applib.main import login_manager

from flask_login import login_user, login_required, logout_user

import urllib
import base64

# +-------------------------+-------------------------+
# +-------------------------+-------------------------+

mod = Blueprint('admin', __name__, url_prefix='/admin')

# +-------------------------+-------------------------+
# +-------------------------+-------------------------+


@mod.route('/login', methods=['POST', 'GET'])
def login():
    
    form = LoginForm(request.form)

    error = None
    if request.method == 'POST' and form.validate():
        username = form.usr_name.data
        password = form.psd_wrd.data

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

                return redirect(url_for('invoice.index'))

            flash(error)


    return render_template('login.html', form=form)



@mod.route("/logout")
@login_required
def logout_app():
    logout_user()
    return redirect(url_for('admin.login'))



@mod.route("/email_receipt")
def report_email_receipt():

    import json 

    """
        ref contains the following values 
            reference=12
            email_type='invoice | receipt | campaign | reminders'  
            email_title='the subject of the email that was sent' 
            email_body="thebodyof themail"         
    """ 
    ref = request.args.get("ref")

    if ref:        
        values = decode_param(ref)
        
        with m.sql_cursor() as db:
            qry = db.query(m.EmailReceipt).filter_by(ref=ref)

            if qry.first():
                qry.update({"counter": qry.first().counter + 1,
                            "last_received": datetime.datetime.now()
                            })                               


            else:
                em = m.EmailReceipt()
                em.ref = ref 
                em.counter = 1 
                em.last_received = datetime.datetime.now()
                em.body = json.dumps(values)
                db.add(em)

                
                dt = datetime.datetime.now().strftime("%b %d %Y %H:%M:%S")
                body = render_template('email_status.html', date_time=dt, **values)
                send_email(None, "support@ecardex.com", "Read Confirmation", body)

    return "OK 200!"

    # send out a confirmation email to support@ecardex.com 











