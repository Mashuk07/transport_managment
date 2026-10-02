import sys, os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from db import get_connection


def main():
    conn = get_connection()
    if not conn:
        print("❌Cannot connect.")
        return
    cur = conn.cursor()

    # Try the insert directly
    sql = """
        INSERT INTO person
            (uiu_id, full_name, designation, email, phone, address)
        VALUES (%s, %s, 'Student', %s, %s, %s)
    """
    params = ("111", "Piya", "piya@bsds.uiu.ac.bd", "1454545", None)

    print("Attempting insert...")
    print(f"  SQL:    {sql.strip()}")
    print(f"  Params: {params}\n")

    try:
        cur.execute(sql, params)
        conn.commit()
        print(f"✅ Inserted. person_id / lastrowid = {cur.lastrowid}")
    except Exception as e:
        print(f"❌ REAL ERROR: {e}")
        import traceback
        traceback.print_exc()

    # Show what's in the table already
    print("\n--- Existing person rows ---")
    cur.execute("SELECT uiu_id, full_name, email FROM person")
    for row in cur.fetchall():
        print(f"  {row}")

    cur.close()
    conn.close()


if __name__ == "__main__":
    main()