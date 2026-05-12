import sqlite3
from pathlib import Path

# Path to the database
DB_PATH = Path(__file__).resolve().parent.parent / "data" / "funnel.db"

def open_database():
    """Open and connect to the SQLite database."""
    try:
        conn = sqlite3.connect(DB_PATH)
        print(f"Successfully connected to database at: {DB_PATH}")
        return conn
    except sqlite3.Error as e:
        print(f"Error connecting to database: {e}")
        return None

def list_tables(conn):
    """List all tables in the database."""
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        print("Tables in the database:")
        for table in tables:
            print(f"  - {table[0]}")
    except sqlite3.Error as e:
        print(f"Error listing tables: {e}")

if __name__ == "__main__":
    conn = open_database()
    if conn:
        list_tables(conn)
        conn.close()
        print("Database connection closed.")