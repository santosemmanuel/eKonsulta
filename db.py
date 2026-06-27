# import mysql.connector
import pymysql.cursors, pymysql
import os
# import sqlite3
from dotenv import load_dotenv

load_dotenv()


def get_db_connection():
    if os.getenv("USE_SQLITE") != 1:
        try:
            conn = pymysql.connect(
                host=os.getenv("DB_HOST"),
                user=os.getenv("DB_USER"),
                port=3306,
                password=os.getenv("DB_PASSWORD"),
                database=os.getenv("DB_NAME"),
                charset='utf8mb4',
                cursorclass=pymysql.cursors.DictCursor
            )
            return conn

        except pymysql.Error as e:
            print("PyMySQL Error:", e)
            return None
    # conn = sqlite3.connect(os.getenv("DB_SQLITE"))
    # conn.row_factory = sqlite3.Row
    # return conn
