"""
db.py - MySQL connection module for USSMS
"""
import mysql.connector
from mysql.connector import Error


# ---- Connection configuration ----
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',              # change if your MySQL user is different
    'password': '1001', # <-- PUT YOUR MYSQL PASSWORD HERE
    'database': 'transport_management',
    'port': 3306
}


def get_connection():
    """Create and return a MySQL connection."""
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        if conn.is_connected():
            return conn
    except Error as e:
        print(f"❌ Error connecting to MySQL: {e}")
        return None


def execute_query(query, params=None, fetch=True):
    """
    Run a query and return results.
    - For SELECT: returns list of rows (fetch=True)
    - For INSERT/UPDATE/DELETE: commits and returns rowcount (fetch=False)
    """
    conn = get_connection()
    if conn is None:
        return None

    cursor = conn.cursor(dictionary=True)  # returns rows as dicts
    try:
        cursor.execute(query, params or ())
        if fetch:
            result = cursor.fetchall()
            return result
        else:
            conn.commit()
            return cursor.rowcount
    except Error as e:
        print(f"❌ Query error: {e}")
        return None
    finally:
        cursor.close()
        conn.close()


def test_connection():
    """Quick test to verify connection works."""
    conn = get_connection()
    if conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM Person")
        count = cursor.fetchone()[0]
        print(f"✅ Connected to TRANSPORT_MANAGEMENT. Person table has {count} rows.")
        cursor.close()
        conn.close()
    else:
        print("❌ Connection failed.")


if __name__ == "__main__":
    test_connection()