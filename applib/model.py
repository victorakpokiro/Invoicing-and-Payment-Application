

import records
from contextlib import contextmanager
from sqlalchemy import (create_engine, Integer, String,
                        Text, DateTime, BigInteger, Date, 
                        Column, ForeignKey, or_, Sequence, func)

import sqlalchemy.dialects.postgresql as ptype
 
from sqlalchemy.ext.declarative import declarative_base  
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager
from applib.lib import helper as h 

from flask_login import UserMixin

import os
from applib.main import db

import datetime

 
# Base = declarative_base()

# +-------------------------+-------------------------+
# +-------------------------+-------------------------+
# old_con_str = 'mysql+mysqldb://root:orobooghene@localhost:3306/invoice'
con_str = h.set_db_uri() 

# +-------------------------+-------------------------+
# +-------------------------+-------------------------+

@contextmanager
def db_session():
    db = records.Database(con_str, echo=True)
    conn = db.get_connection()
    tx = conn.transaction()

    try:    
        yield conn
        tx.commit()
    
    except Exception as e:
        tx.rollback()
        raise e 
        # log the error here 
    
    finally:
        conn.close()

# +-------------------------+-------------------------+
# +-------------------------+-------------------------+

@contextmanager  
def sql_cursor():

    try:         
        yield db.session
        db.session.commit()
    except Exception as e:  
        db.session.rollback()    
        raise e 

        # if in dev environment raise error else log to file or smtp.
        
        # if os.getenv("env", None) == 'dev':
        #     raise e

        # lg = logs.get_logger('db_error', is_debug=True)
        # lg.exception(g.domain)
        
    finally:
        db.session.close()

# +-------------------------+-------------------------+
# +-------------------------+-------------------------+

class Users(UserMixin, db.Model):
    __tablename__ = 'users'

    id = Column(BigInteger, Sequence('users_id_seq'), primary_key=True)    
    username = Column(String(150), nullable=True)
    password = Column(String(150), nullable=True)     


class Invoice(db.Model):

    __tablename__ = "invoice"

    inv_id = Column(BigInteger, Sequence('invoice_inv_id_seq'), primary_key=True)    
    disc_type = Column(String(10))    
    disc_value = Column(String(10))   
    purchase_no = Column(Integer)  
    invoice_no = Column(String(30))   
    date_value = Column(DateTime())  
    invoice_due = Column(DateTime())
    client_type = Column(Integer, nullable=False)
    currency  = Column(Integer, nullable=False) 
    client_id =  db.Column(db.BigInteger, db.ForeignKey('client.id'), nullable=False)
    payment = db.relationship('Payment', backref='client', lazy=True)
    item = db.relationship('Items', backref='invoice', lazy=True)


class Items(db.Model):

    __tablename__ = "item"

    id = Column(BigInteger, Sequence('item_id_seq'), primary_key=True) 
    item_desc = Column(String(150), nullable=False)
    qty = Column(Integer, nullable=False)
    rate = Column(Integer, nullable=False)
    amount = Column(String(30))
    invoice_id = db.Column(db.BigInteger, db.ForeignKey('invoice.inv_id'),
        nullable=False)


class EmailQueue(db.Model):

    __tablename__ = "email_queue"

    id = Column(BigInteger, Sequence('email_queue_id_seq'), primary_key=True)
    field= Column(String(150))
    reference= Column(String(150))
    date_created= Column(DateTime())
    status= Column(Integer)


class Client(db.Model):
    
    __tablename__ = "client"

    id = Column(BigInteger, Sequence('client_invoice_id_seq'), primary_key=True)
    name = Column(String(150), nullable=False)
    address = Column(Text, nullable=False)    
    email = Column(String(150), nullable=False) 
    phone = Column(String(20), nullable=False)        
    post_addr = Column(String(20), nullable=False) 
    date_created = Column(DateTime(), nullable=False)
    invoice = db.relationship('Invoice', backref='client', lazy=True)
 


class Expense(db.Model):

    __tablename__ = "expense"

    id = Column(BigInteger, Sequence('expense_id_seq'), primary_key=True)
    title = Column(String(100))
    desc = Column(Text)
    date_created = Column(DateTime, nullable=False, 
                          default=datetime.datetime.now())
    
    requested_by = Column(String(100), nullable=False)

    # status =1 for pending, 2 for approved and 3 for declined 
    status = Column(Integer, nullable=False, default=0)
    aproved_by = Column(String(100), nullable=False)
    amount = Column(String(100), nullable=False)


class Payment(db.Model):

    __tablename__ = 'payment'

    id = Column(BigInteger, Sequence('payment_id_seq'), primary_key=True)
    client_name = Column(String(150), nullable=False)
    payment_desc = Column(Text)
    date_created = Column(DateTime, nullable=False, 
                          default=datetime.datetime.now())
    payment_mode = Column(Integer, nullable=False)
    amount_paid = Column(String(30))
    balance = Column(String(30))
    invoice_id = db.Column(db.BigInteger, db.ForeignKey('invoice.inv_id'), nullable=False)
    status = Column(Integer, nullable=False, default=0)


class EmailReceipt(db.Model):

    __tablename__ = 'email_receipt_count'

    id = Column(BigInteger, Sequence('email_receipt_id_seq'), primary_key=True)
    ref = Column(String(240), nullable=False)
    counter = Column(BigInteger, nullable=False)
    last_received = Column(DateTime, nullable=False)
    body = Column(String(240))




def form2model(formobj, model_ins):
    counter = 0            
    for key, obj in formobj._fields.items():
        if hasattr(model_ins, key):
            setattr(model_ins, key, obj.data)
            counter += 1 

    assert counter > 0 , "No model instance fields not found."
     
def model2form(model_ins, form_ins):

    counter = 0
    for key, obj in form_ins._fields.items():
        if hasattr(model_ins, key):
            obj.data = getattr(model_ins, key)
            counter += 1

    assert counter > 0 , "No model instance fields not found."
