from applib.model import db_session
import records



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