from dotenv import load_dotenv
import os
import mysql.connector

load_dotenv()

def obtener_conexion():
    return mysql.connector.connect(
        host=os.getenv('DB_HOST'),
        database=os.getenv('DB_NAME'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD'),
        charset='utf8mb4'
    )
