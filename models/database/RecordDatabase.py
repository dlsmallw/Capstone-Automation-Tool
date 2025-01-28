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
            self.conn = db.connect(uri, check_same_thread=False, uri=True)
            self.cursor = self.conn.cursor()
        except db.OperationalError:
            self.conn = db.connect(filepath, check_same_thread=False)
            self.cursor = self.conn.cursor()
            with open('./models/database/schema.sql', 'r') as sql_schema:
                sql_script = sql_schema.read()
                self.cursor.executescript(sql_script)
                self.conn.commit()
            
    def close(self):
        if self.conn:
            self.conn.close()

    def validate_table_exists(self, table_name) -> bool:
        self.cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?;",
            ([table_name])
        )
        result = self.cursor.fetchone()
        return result is not None

    def insert(self, table, data):
        if self.validate_table_exists(table):
            columns = ', '.join(data.keys())
            placeholders = ', '.join('?' * len(data))
            query = f"INSERT INTO {table} ({columns}) VALUES ({placeholders});"
            self.cursor.execute(query, tuple(data.values()))
            self.conn.commit()
            return True
        return False

    def update(self, table, data, conditions=None):
        if self.validate_table_exists(table):
            exe_args = tuple(data.values())

            set_placeholder = ''
            for key in data.keys():
                if set_placeholder == '':
                    set_placeholder += f'{key} = ?'
                else:
                    set_placeholder += f', {key} = ?'

            conditions_placeholder = ''
            if conditions is not None:
                conditions_placeholder = ' WHERE '
                for key in conditions.keys():
                    if conditions_placeholder == ' WHERE ':
                        conditions_placeholder += f'{key} = ?'
                    else:
                        conditions_placeholder += f'AND {key} = ?'
                
                exe_args = exe_args + tuple(conditions.values())

            query = f"UPDATE {table} SET {set_placeholder}{conditions_placeholder};"
            self.cursor.execute(query, exe_args or ())
            self.conn.commit()
            return True
        return False

    def remove(self, table, conditions):
        if self.validate_table_exists(table):
            conditions_placeholder = ' WHERE '
            for key in conditions.keys():
                if conditions_placeholder == ' WHERE ':
                    conditions_placeholder += f'{key} = ?'
                else:
                    conditions_placeholder += f'AND {key} = ?'
            
            query = f"DELETE FROM {table}{conditions_placeholder};"
            self.cursor.execute(query, tuple(conditions.values()))
            self.conn.commit()
            return True
        return False

    def select(self, table, cols=None, conditions=None):
        if self.validate_table_exists(table):
            exe_args = None
            if cols is not None:
                columns = ', '.join(cols)
            else:
                columns = '*'

            conditions_placeholder = ''
            if conditions is not None:
                conditions_placeholder = ' WHERE '
                for key in conditions.keys():
                    if conditions_placeholder == ' WHERE ':
                        conditions_placeholder += f'{key} = ?'
                    else:
                        conditions_placeholder += f'AND {key} = ?'

                exe_args = tuple(conditions.values())
            
            query = f"SELECT {columns} FROM {table}{conditions_placeholder};"
            self.cursor.execute(query, exe_args or ())
            return self.cursor.fetchall()
        return None
    
    def select_joined(self, base_table, join_clauses, select_columns='*', conditions=None, params=None):
        query = f"SELECT {select_columns} FROM {base_table}"

        for join_type, table, on_condition in join_clauses:
            query += f" {join_type.upper()} JOIN {table} ON {on_condition}"

        if conditions:
            query += f" WHERE {conditions}"

        try:
            self.cursor.execute(query, params or ())
            return self.cursor.fetchall()
        except Exception as e:
            exc_type = type(e),__name__
            exc_cause = 'No Cause/Context Provided'
            cause = e.__cause__ or e.__context__
            if cause:
                exc_cause = str(cause)
            
            print(f'{exc_type}: {exc_cause}')
            return None

    def inv_val_to_none(self, df: pd.DataFrame):
        df.replace(['', 'None', 'nan', 'NaN', np.nan, None], pd.NA, inplace=True)
    
    def table_to_df(self, table_name) -> pd.DataFrame:
        df = None
        if self.validate_table_exists(table_name):
            query = f'SELECT * FROM {table_name}'
            df = pd.read_sql_query(query, self.conn)
            self.inv_val_to_none(df)
        return df

    def df_to_table(self, table, df: pd.DataFrame):
        if self.validate_table_exists(table):
            try:
                df.to_sql(table, self.conn, if_exists='replace', index=False)
                return True
            except:
                return False
        return False

    def encrypt(self, items: tuple[str | None]):
        results = []
        for item in items:
            results.append(base64.b64encode(item.encode('utf-8')) if item is not None and item != '' else 'NULL')
        return tuple(results)
    
    def decrypt(self, items: tuple[str | None]):
        results = []
        for item in items:
            results.append(base64.b64decode(item).decode('utf-8') if item is not None and item != '' else None)
        return tuple(results)

    def get_avail_taiga_projects(self):
        cols = ['id', 'project_name', 'project_owner']
        projects = self.select('taiga_projects', cols)[0]
        return projects