

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
    client_type = Column(String(150), nullable=False)
    description = Column(String(350), nullable=True) 
    currency  = Column(String(3), nullable=False) 
    client_id =  db.Column(db.BigInteger, db.ForeignKey('client.id'), nullable=False)
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


class Email_queue(db.Model):

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
    invoice = db.relationship('Invoice', backref='client', lazy=True)
 

        





     
    