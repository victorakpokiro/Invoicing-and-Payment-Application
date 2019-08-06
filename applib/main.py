
from flask import Flask, request
from applib.api import InvoiceApi 
from flask_restful import Api
from applib.model import db_session 
import records
import json


from applib.sub_routes.admin import mod 
import applib.sub_routes.admin as ad 

# +-------------------------+-------------------------+
# +-------------------------+-------------------------+

app = Flask(__name__)
api = Api(app)

# +-------------------------+-------------------------+
# +-------------------------+-------------------------+
 
 
app.register_blueprint(ad.mod)

api.add_resource(InvoiceApi, '/invoice/gen', methods=['POST'])

 
 