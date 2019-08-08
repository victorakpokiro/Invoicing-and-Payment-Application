
from flask_restful import Resource, Api, request
import json
import arrow


# +-----------------------+---------------------------+
# +-----------------------+---------------------------+

from applib.model import db_session
from applib.forms import (CustomerForm, ItemForm, BillsForm)


 
class InvoiceApi(Resource):

    def post(self):

        with db_session() as db:

            inbound_data = json.loads(request.data.decode('utf-8')) 

            invoice_data = inbound_data['Invoice']

            customer = invoice_data['customer']
            items = invoice_data['items']
            billing = invoice_data['bills']

            customer_form = CustomerForm(**customer)
            customer_is_valid = customer_form.validate()
               
            billing_form = BillsForm(**billing)
            billing_is_valid = billing_form.validate()
            
            
            for values in items: 
                item_form = ItemsForm(**values)
                item_is_valid = item_form.validate()
                
             
            # return feedback for form errors if there exists an error 
            if not customer_is_valid or not billing_is_valid or not item_is_valid:
                all_error = customer_form.errors, billing_form.errors, item_form.errors           
                return self.response(json.dumps(all_error)), 400
                    

            # if the code get here all is well
            
            sub_total_amount = 0
            for item in items:
                sub_total_amount += float(item['amount'])
          
            date = arrow.now().format('YYYY-MM-DD')
            
            rows = db.query('select count(*) as count from invoice')
            rows_count_numb = (rows[0].count + 1) if rows.all() else 1

            
            rows = db.query('select count(*) as count from item')
            rows1_count_numb = (rows[0].count + 1)  if rows.all() else 1

            total_amt = self.get_total(
                            sub_total_amount, 
                            billing['disc_value'], 
                            billing['disc_type'])
    

            balance_amt = total_amt - float(billing['amtPaid'])     
            _json_obj_invoice = {
                'name': customer['name'],
                'address': customer['address'],
                'email': customer['email'],
                'phone': customer['phone'],
                'postaladdress': customer['postal_code'],
                'disc_type': billing['disc_type'],
                'disc_value': billing['disc_value'],
                'purchase_no': rows_count_numb,
                'invoiceno': 'INV-' + str(rows_count_numb),
                'datevalue': date,
                'invoicedue': date,
                'amtPaid': billing['amtPaid'],  
                'balance': balance_amt,
                'subtotal': sub_total_amount,
                'total': total_amt,
                'currency': billing['currency']
                }


            sql_insert_invoice_table = """INSERT INTO invoice ( name, address, email, phone, post_addr, disc_type, 
                                                      disc_value, purchase_no, invoice_no, date_value, 
                                                      invoice_due, paid_to_date, balance, sub_total, total, currency)
                                                VALUES ( :name, :address, :email, :phone, :postaladdress, 
                                                        :disc_type, :disc_value, :purchase_no, :invoiceno, 
                                                        :datevalue, :invoicedue, :amtPaid, :balance, :subtotal, 
                                                        :total, :currency )"""
          
            resp = db.query(sql_insert_invoice_table, **_json_obj_invoice)

            #recheck this for postgres syntax
            last_id = db.query('SELECT last_insert_id() as id')
            _id = last_id.all()[0].id
            
            self.move_items2tbl(db, _id, items) #  why is this line like this 
            

            _json_email_queue = {
                'reference': _id,
                'date_created': date,
                'status': 0,
                'field': 'invoice'
            }

            sql_insert_email_queue = """INSERT INTO email_queue ( field, reference, date_created, status )
                            VALUES ( :field, :reference, :date_created, :status )
                            """

            db.query(sql_insert_email_queue, **_json_email_queue)


        return {'status': 'Success'}, 200



    def get_total(self, item_total, dis_value, dis_type):

        calc_total = 0 

        if dis_type == 'fixed':
            calc_total = item_total - float(dis_value)

        elif dis_type == 'percentage':
            calc_total = item_total - float(dis_value) /100.0 *  item_total

        return round(calc_total, 2) 


    def response(self, msg, code=-1):   

        """
            code is -1 when there is an error
            code is 0 when the is no error ie success message 
            msg dscribes the issue for the error
        """

        return {
            'resp_code': code,
            'resp_msg': msg
        }


    def move_items2tbl(self, db, invoice_id, itemobj):

        _sql = """INSERT INTO item ( item_desc, qty, rate, amount, invoice_id)
                  VALUES ( :desc, :qty, :rate, :amount, :invoiceid )
              """
      
        for item in itemobj:
            item['invoiceid'] = invoice_id            
            row1 = db.query(_sql, **item)
            # db.flush()



 

       
