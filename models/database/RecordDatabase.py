import sqlite3 as db
import numpy as np
import pandas as pd
from urllib.request import pathname2url
import base64
import os


class RecDB:
    conn = None
    cursor = None

    def __init__(self, db_filepath='./models/database/capstone_data.db'):
        self.__connect_or_create_db(db_filepath)
        
    def __connect_or_create_db(self, filepath):
        try:
            uri = 'file:{}?mode=rw'.format(pathname2url(filepath))
            self.conn = db.connect(uri, uri=True)
            self.cursor = self.conn.cursor()
        except db.OperationalError:
            with open('./models/database/schema.sql', 'r') as sql_schema:
                sql_script = sql_schema.read()

            self.conn = db.connect(filepath)
            self.cursor = self.conn.cursor()
            self.cursor.executescript(sql_script)
            self.conn.commit()
            
    def close(self):
        if self.conn:
            self.conn.close()

    def validate_table_exists(self, table_name) -> bool:
        self.cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?;",
            (table_name)
        )
        result = self.cursor.fetchone()
        return result is not None
    
    def inv_val_to_none(self, df: pd.DataFrame):
        df.replace(['', 'None', 'nan', 'NaN', np.nan], [None, None, None, None, None], inplace=True)
    
    def table_to_df(self, table_name) -> pd.DataFrame:
        df = None
        if self.validate_table_exists(table_name):
            query = f'SELECT * FROM {table_name}'
            df = pd.read_sql_query(query, self.conn)
            self.inv_val_to_none(df)
        return df
    
    def remove_entries_by_id(self, table_name, id_list):
        if self.validate_table_exists(table_name) and id_list:
            id_str = ", ".join(["?"] * len(id_list))
            self.cursor.execute(
                "DELETE FROM ? WHERE id IN (?);",
                (table_name, id_str)
            )
            num_rows_del = self.cursor.rowcount
            self.conn.commit()
            return num_rows_del
        return 0
    
    def update_table_with_df(self, table_name, df: pd.DataFrame):
        if self.validate_table_exists(table_name) and df:
            df.to_sql(table_name, self.conn, if_exists='replace', index=False)
        self.conn.commit()

    def encrypt(self, val: str):
        return base64.b64encode(val.encode('utf-8')) if val is not None and val != '' else 'NULL'
    
    def decrypt(self, val: str):
        return base64.b64decode(val).decode('utf-8') if val is not None and val != '' else None

    def update_user_credentials(self, site_name, username=None, password=None, token=None):
        encrypted_uname = self.encrypt(username) 
        encrypted_pwd = self.encrypt(password) 
        encrypted_token = self.encrypt(token) 

        self.cursor.execute(
            "UPDATE sites SET user_name=?, user_pwd=?, site_token=? WHERE site_name=?;",
            (encrypted_uname, encrypted_pwd, encrypted_token, site_name)
        )

        print('Test1')
        self.conn.commit()

    def get_user_credential_for_site(self, site_name):
        query = f"SELECT user_name, user_pwd, site_token FROM sites WHERE site_name='{site_name}';"
        self.cursor.execute(query)
        encrypted_uname, encrypted_pwd, encrypted_token = self.cursor.fetchall()[0]
        uname = self.decrypt(encrypted_uname)
        pwd = self.decrypt(encrypted_pwd)
        token = self.decrypt(encrypted_token)
        return uname, pwd, token
