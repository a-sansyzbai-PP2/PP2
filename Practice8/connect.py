import psycopg2
from config import DB_SETTINGS

def open_db():
    return psycopg2.connect(**DB_SETTINGS)