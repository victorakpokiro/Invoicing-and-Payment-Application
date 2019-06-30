
from configobj import ConfigObj

from passlib.hash import pbkdf2_sha256

from flask import session 
import datetime
 

# +-------------------------+-------------------------+
# +-------------------------+-------------------------+


def get_config(header, key=None, filename='config.ini'):

    cfg = ConfigObj(filename)
    if not key:
        return cfg[header]

    return cfg[header][key]


# +-------------------------+-------------------------+
# +-------------------------+-------------------------+


class SetUri:
    """
        # default uri 
        # dialect+driver://username:password@host:port/database

        # default uri 
        # dialect+driver://username:password@host:port/database

        # postgresql uri structure 
        >>> postgresql://scott:tiger@localhost:5432/mydatabase 
        # sqlite uri structure 
        >>> sqlite:///foo.db

    """

    def __init__(self, db_cfg):
        self.db_cfg = db_cfg


    def set_credentials(self):
        tmp = self.db_cfg
        output = ''
        
        if tmp['username']:
            output = tmp['username'] + ':' + tmp["password"]

        return output


    def set_connections(self):
        
        output = ''

        if self.db_cfg['host']:
            output = '@'+ self.db_cfg['host'] + ':' + self.db_cfg['port']

        return output


    def set_db(self):        
        return  '/' + self.db_cfg['database']


    def set_driver(self):
        output = self.db_cfg['dialect'] 
        if self.db_cfg.get('driver', None):
            output += '+' + self.db_cfg['driver']

        output += '://'

        return output


    def run(self):
        
        return (self.set_driver() + self.set_credentials() 
                + self.set_connections() + self.set_db()
                )



def set_db_uri():

    _db_cfg = get_config('db')
    uri = SetUri(_db_cfg)
    return uri.run()

# +-------------------------+-------------------------+
# +-------------------------+-------------------------+


def encrypt_passwd(passwd):
    return pbkdf2_sha256.hash(passwd)


def validate_hash(passwd, hash):
    if not passwd or not hash:
        return False

    return pbkdf2_sha256.verify(passwd.encode('utf-8'), hash.encode('utf-8'))

# +-------------------------+-------------------------+
# set and delete session 
# +-------------------------+-------------------------+

# def set_session(site, name, val):
#     session['%s_%d'%(name, site)] = val


# def del_session(site, name):
#     del session['%s_%d'%(name, site)]

# def get_session(site, name):
#     return session['%s_%d'%(name, site)]

# +-------------------------+-------------------------+
# +-------------------------+-------------------------+


def date_format(date_obj, strft='%H: %M: %S'):
    
    now = datetime.datetime.now()
    diff = now - date_obj

    if diff.days == 0:
        retv = date_obj.strftime(strft)

    elif diff.days == 1:
        retv = 'Yesterday'

    elif diff.days > 1 and diff.days < 10:
        retv = date_obj.strftime('%d, %B')

    else:
        retv = date_obj.strftime("%d-%m-%Y")
    

    return retv


