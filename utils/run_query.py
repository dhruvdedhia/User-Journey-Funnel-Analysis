import sqlite3
from pathlib import Path

# Path to the database
DB_PATH = Path(__file__).resolve().parent.parent / "data" / "funnel.db"

def run_query(query):
    """Run a SQL query on the database and print results."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(query)
        results = cursor.fetchall()

        # Get column names
        column_names = [description[0] for description in cursor.description]

        print("Query Results:")
        print("-" * 50)
        # Print header
        print(" | ".join(column_names))
        print("-" * 50)
        # Print rows
        for row in results:
            print(" | ".join(str(cell) for cell in row))

        conn.close()
        print(f"\nQuery executed successfully. {len(results)} rows returned.")

    except sqlite3.Error as e:
        print(f"Error executing query: {e}")

if __name__ == "__main__":
    query = """
    SELECT
        location,
        event,
        COUNT(DISTINCT user_id) AS users
    FROM events
    GROUP BY location, event
    ORDER BY location, users DESC;
    """
    run_query(query)