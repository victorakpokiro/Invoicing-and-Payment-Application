
import os
import argparse

from applib.main import app, db
from applib.lib.helper import get_config, set_db_uri


# +-------------------------+-------------------------+
# +-------------------------+-------------------------+

def main():

    cmd = get_commands()

    if cmd.create_tl:
        db.create_all()
        print("all missing tables have been recreated from scratch")
        return

    if cmd.drop_tl:
        db.drop_all()
        print("all tables dropped from the database")
        return

    # main app starts here
    app.config.update(get_config('server'))
    app.run()


def get_commands():
    parser = argparse.ArgumentParser()

    parser.add_argument('-c', "--create_tl", action='store_true',
                        help='pass this argument to create missing tables',
                        default=False)

    parser.add_argument('-d', "--drop_tl", action='store_true',
                        help='pass this argument to drop all existing tables',
                        default=False)

    return parser.parse_args()


# +-------------------------+-------------------------+
# +-------------------------+-------------------------+

if __name__ == '__main__':
    main()
