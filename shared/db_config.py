import mysql.connector
import os
from dotenv import load_dotenv
<<<<<<< HEAD
import sqlite3
=======

>>>>>>> 38ca3952210f03e69c56af4b3734e2c395073b4a
load_dotenv()

def get_db_connection():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST", "localhost"),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD", ""),
        database=os.getenv("DB_NAME", "smart_recruitment_chatbot")
    )
