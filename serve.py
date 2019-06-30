
import os 


from applib.main import app 
from applib.model import db_session 
from applib.lib.helper import get_config


# +-------------------------+-------------------------+
# +-------------------------+-------------------------+

def main(): 
 
    folder = 'table'    

    tables = get_config('tables', 'order')
    
    with db_session() as db:
        for _file in tables:
            _f = os.path.join(folder, '%s.sql'%_file)

            with open(_f, 'r') as fl:
                db.query(fl.read())


    app.config.update(get_config('server'))
    # add the wsgi layer here be running the production code 
    app.run()



# +-------------------------+-------------------------+
# +-------------------------+-------------------------+


if __name__ == '__main__':
    main()



