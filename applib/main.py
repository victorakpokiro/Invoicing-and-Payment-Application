
import json
import records

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
import applib.sub_routes.admin as ad 

api = Api(app)


@login_manager.user_loader
def load_user(user_id):
    # since the user_id is just the primary key of our user table, 
    # use it in the query for the user
    return m.Users.query.get(user_id)  


# +-------------------------+-------------------------+
# +-------------------------+-------------------------+
 
app.register_blueprint(ad.mod)
api.add_resource(InvoiceApi, '/invoice/gen', methods=['POST'])

 
 