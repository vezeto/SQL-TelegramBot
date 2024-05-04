import sqlite3
import logging

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')


class Database:
    def __init__(self, db_name='users.db'):
        self.conn = sqlite3.connect(db_name)
        self.conn.execute("PRAGMA foreign_keys = ON")  # Turning on foreign key constraints
        self.cur = self.conn.cursor()

    # def create_cursor(self):
    #     self.cur = self.conn.cursor()

    def create_table(self):
        query1 = '''
        CREATE TABLE IF NOT EXISTS users(
            id INTEGER PRIMARY KEY,
            chat_id INTEGER,
            username TEXT,
            first_name TEXT,
            last_name TEXT
        )
        '''

        query2 = '''
        CREATE TABLE IF NOT EXISTS subs(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            name TEXT,
            mode TEXT,
            period TEXT,
            date DATE,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE ON UPDATE CASCADE
        )
        '''
        with self.conn:
            self.cur.execute(query1)
            self.cur.execute(query2)
            self.conn.commit()

    def list_subs(self, user_id_to_show):
        query = '''
        SELECT * FROM subs
        WHERE user_id = ?
        '''
        value = (user_id_to_show,)
        self.cur.execute(query, value)
        subs_to_show = self.cur.fetchall()
        return subs_to_show

    def add_user(self, user_info):
        query = '''
        INSERT INTO users (id, chat_id, username, first_name, last_name)
        VALUES (?, ?, ?, ?, ?)
        '''
        values = (user_info.user_id, user_info.chat_id, user_info.username, user_info.first_name, user_info.last_name)
        with self.conn:
            self.cur.execute(query, values)
            self.conn.commit()

    def in_users(self, user_id_to_check):
        query = '''
        SELECT * FROM users
        WHERE id = ?
        '''
        value = (user_id_to_check,)
        self.cur.execute(query, value)
        user = self.cur.fetchone()
        # print(user)
        return user is not None  # return True, if user is found

    def add_sub(self, sub_info):
        query = '''
        INSERT INTO subs (user_id, name, mode, period, date)
        VALUES (?, ?, ?, ?, ?)
        '''
        values = (sub_info.user_id, sub_info.sub_name, sub_info.sub_mode, sub_info.period, sub_info.date)
        with self.conn:
            self.cur.execute(query, values)
            self.conn.commit()

    def delete_user(self, user_id_to_delete):
        query = 'DELETE FROM users WHERE id = ?'
        value = (user_id_to_delete,)
        try:
            with self.conn:
                self.cur.execute(query, value)
                self.conn.commit()
                logging.info(f"User with ID {user_id_to_delete} deleted successfully.")
        except Exception as e:
            logging.error(f"Error occurred while deleting user with ID {user_id_to_delete}: {e}")

    # def
    # def delete_sub(self, sub_id_to_delete):
    #     query = 'DELETE FROM subs WHERE id = ?'

    def close(self):
        self.conn.close()
