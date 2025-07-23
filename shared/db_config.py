import mysql.connector

def get_db_connection():
    return mysql.connector.connect(
        host="sql12.freesqldatabase.com",
        user="sql12791501",
        password="dhnRt9XWpu",
        database="sql12791501",
        port=3306
    )
