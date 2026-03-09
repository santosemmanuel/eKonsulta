import mysql.connector
import os
import sqlite3
from dotenv import load_dotenv

load_dotenv()

def get_db_connection():
    if os.getenv("USE_SQLITE") != 1 :
        # return mysql.connector.connect(
        #     host=os.getenv("DB_HOST"),
        #     user=os.getenv("DB_USER"),
        #     password=os.getenv("DB_PASSWORD"),
        #     database=os.getenv("DB_NAME")
        # )
        pass
    conn = sqlite3.connect(os.getenv("DB_SQLITE"))
    conn.row_factory = sqlite3.Row
    return conn