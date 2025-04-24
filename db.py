import os
from dotenv import load_dotenv
import mysql.connector

load_dotenv()

def get_db():
    cfg = {
        "host":     os.getenv("MYSQL_HOST"),
        "port":     int(os.getenv("MYSQL_PORT", 3306)),
        "user":     os.getenv("MYSQL_USER"),
        "password": os.getenv("MYSQL_PASSWORD"),
        "database": os.getenv("MYSQL_DATABASE"),
    }
    print("⛓️ Connecting to MySQL with:", cfg)
    return mysql.connector.connect(**cfg)
