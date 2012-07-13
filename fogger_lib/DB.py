from os import path as op
import sqlite3 as sq

from gi.repository import GLib

DB_PATH = op.join(GLib.get_user_cache_dir(), 'fogger')
DEFAULT_WIDTH = 1024
DEFAULT_HEIGHT = 768
DEFAULT_STATE = False # True if maximized


class StateDB(object):
    _con = None
    def __init__(self):
        db_path = op.join(DB_PATH, 'state.db')
        self._con = sq.connect(db_path)
        cursor = self._con.cursor()
        cursor.execute('CREATE TABLE IF NOT EXISTS WINDOW_STATE(id string primary key, width int, height int, maximized bool)')
        self._con.commit()

    def __del__(self):
        self._con.close()

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

