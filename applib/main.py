
import json
# import records

from flask import Flask, request
from flask_restful import Api


from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy


from applib.lib import helper  as h 
 
# +-------------------------+-------------------------+
# +-------------------------+-------------------------+

app = Flask(__name__)

app.config.update({
                    "SQLALCHEMY_DATABASE_URI": h.set_db_uri(),
                    'SQLALCHEMY_ECHO': True,
                    'SQLALCHEMY_TRACK_MODIFICATIONS': False
                  })

db = SQLAlchemy(app)

  
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.session_protection = "strong"
login_manager.login_view = 'admin.login'

# declared here so that the db object would be set before introducing the model module

from applib import model as m 
from applib.api import InvoiceApi 

import applib.sub_routes.admin as adm
import applib.sub_routes.client as clt
import applib.sub_routes.expense as exp  
import applib.sub_routes.invoice as inv
import applib.sub_routes.item as itm
import applib.sub_routes.payment as pay


api = Api(app)


@login_manager.user_loader
def load_user(user_id):
    # since the user_id is just the primary key of our user table, 
    # use it in the query for the user
    return m.Users.query.get(user_id)  


# +-------------------------+-------------------------+
# +-------------------------+-------------------------+
 

app.register_blueprint(adm.mod)
app.register_blueprint(clt.mod)
app.register_blueprint(exp.mod)
app.register_blueprint(inv.mod)
app.register_blueprint(itm.mod)
app.register_blueprint(pay.mod)


api.add_resource(InvoiceApi, '/invoice/gen', methods=['POST'])

 
 