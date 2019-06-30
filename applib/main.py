
from flask import Flask, request
from applib.api import InvoiceApi 
from flask_restful import Api
from applib.model import db_session 
import records
import json


# +-------------------------+-------------------------+
# +-------------------------+-------------------------+

app = Flask(__name__)
api = Api(app)

# +-------------------------+-------------------------+
# +-------------------------+-------------------------+
 

	



api.add_resource(InvoiceApi, '/invoice/gen', methods=['POST'])

 
 