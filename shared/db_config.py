import mysql.connector

def get_db_connection():
    return mysql.connector.connect(
        host="sql12.freesqldatabase.com",
        user="sql12792866",
        password="l8299HMdQ9",
        database="sql12792866",
        port=3306
    )
