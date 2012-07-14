from os import path as op
import sqlite3 as sq
import logging
logger = logging.getLogger('fogger_lib')

from gi.repository import GLib

from . helpers import get_or_create_directory

DB_PATH = op.join(GLib.get_user_cache_dir(), 'fogger')
DEFAULT_WIDTH = 1024
DEFAULT_HEIGHT = 768
DEFAULT_STATE = False # True if maximized


class FailSafeClass(object):
    '''
    This class acts as a dummy object and can be used in place of any other
    class. Used to safely fallback to default or dummy values in case
    non-mission critical objects fail to operate
    '''
    DEFAULT_VALUES = {
        'load_state': (DEFAULT_WIDTH, DEFAULT_HEIGHT, DEFAULT_STATE),
        'fetchone': None,
    }

    def __init__(self, name=None):
       self.name = name

    def __getattr__(self, attr):
        logger.debug('FailSafe class emulated %s' % attr)
        return FailSafeClass(attr)

    def __call__(self, *args, **kwargs):
        if self.name in self.DEFAULT_VALUES:
            value = self.DEFAULT_VALUES[self.name]
            logger.debug('FailSafe class returned %s for %s' % (value, self.name))
            return value
        else:
            logger.debug('FailSafe emulated call for  %s' % self.name)
            return FailSafeClass()


class StateDB(object):
    _con = FailSafeClass()

    def __new__(cls):
        #db_path = op.join(get_or_create_directory(DB_PATH), 'state.db')
        #db_path = op.join(DB_PATH, 'state.db')
        db_path = op.join('/home/owais/Desktop/kuta/', 'state.db')

        try:
            if (cls._con == None) or isinstance(cls._con, FailSafeClass):
                cls._con = sq.connect(db_path)
                cursor = cls._con.cursor()
                cursor.execute('CREATE TABLE IF NOT EXISTS WINDOW_STATE(id string primary key, width int, height int, maximized bool)')
                cls._con.commit()
                return object.__new__(cls)
        except sq.OperationalError:
            logger.error('Could not connect to the database: %s' % db_path)
            return FailSafeClass()

    def load_state(self, uuid):
        cursor = self._con.cursor()
        cursor.execute("SELECT * FROM WINDOW_STATE WHERE id=?", (uuid,))
        state = cursor.fetchone()
        if state:
            return (state[1], state[2], state[3] != 0,)
        else:
            return (DEFAULT_WIDTH, DEFAULT_HEIGHT, DEFAULT_STATE)

    def save_state(self, *values):
        cursor = self._con.cursor()
        cursor.execute("REPLACE INTO WINDOW_STATE (id, width, height, maximized) VALUES (?,?,?,?)", values)
        self._con.commit()

state_db = None
def get_state_db():
    global state_db
    state_db = state_db or StateDB()
    return state_db
