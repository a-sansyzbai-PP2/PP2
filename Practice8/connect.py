# connect.py
import psycopg2
from config import DB_CONFIG


def get_connection():
    """Create and return a PostgreSQL connection."""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except psycopg2.OperationalError as e:
        print(f"[ERROR] Could not connect to the database:\n  {e}")
        return None


if __name__ == "__main__":
    conn = get_connection()
    if conn:
        with conn.cursor() as cur:
            cur.execute("SELECT version();")
            print("[OK]", cur.fetchone()[0])
        conn.close()