import mysql.connector


def get_connection():
    connection = mysql.connector.connect(
        host="localhost",
        user="root",
        password="5551",
        database="healthcare_analytics"
    )

    return connection