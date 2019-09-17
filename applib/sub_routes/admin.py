
import os
import subprocess
import datetime

from flask import (Blueprint, request, url_for, 
                   render_template, redirect, session, flash)


from werkzeug.security import check_password_hash, generate_password_hash
from applib.forms import LoginForm

from applib.model import db_session
from applib import model as m 
from applib.lib.helper import get_config 

# from applib.main import login_manager

from flask_login import login_user, login_required, logout_user

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







