

import records
from contextlib import contextmanager

from applib.lib import helper as h 


# 'mysql+mysqldb://root:orobooghene@localhost:3306/invoice'
con_str = h.set_db_uri() 


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


     
    