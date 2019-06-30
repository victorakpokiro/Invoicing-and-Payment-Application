# # import pudb;pudb.set_trace()
# from applib.api import InvoiceApi
# from applib.model import db_session 
# import records
# import arrow
# from odserver import sample
# import smtplib, ssl

# date = arrow.now().format('YYYY-MM-DD')



# with db_session() as db:
    
#     resp = db.query("""select inv_id from invoice order by inv_id desc 
#                         limit 1 
#                     """)   
    
#     output = resp.all() 
#     last_id = output[0].inv_id 

#     _json_email_queue = {
#         'reference': last_id,
#         'date_created': date,
#         'status': 0

#         }

#     if _json_email_queue['status'] == 0:
#         _json_email_queue['field'] = 'invoice'

#     sql_insert_email_queue = """INSERT INTO email_queue ( field, reference, date_created, status )
#                                 VALUES ( :field, :reference, :date_created, :status )
#                                 """


#     db.query(sql_insert_email_queue, **_json_email_queue)
    
    
    
#     