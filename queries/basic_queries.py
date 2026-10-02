import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from db import get_connection


def run_query(sql, title):
    print(f"\n{'='*70}")
    print(f"  {title}")
    print('='*70)
    conn = get_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute(sql)
    rows = cur.fetchall()
    if not rows:
        print("   (no results)")
    else:
        # Print headers
        headers = list(rows[0].keys())
        print("   " + " | ".join(f"{h[:20]:20s}" for h in headers))
        print("   " + "-" * (23 * len(headers)))
        for r in rows[:30]:
            print("   " + " | ".join(f"{str(r[h])[:20]:20s}" for h in headers))
        if len(rows) > 30:
            print(f"   ... {len(rows) - 30} more rows")
    print(f"\n   Rows: {len(rows)}")
    cur.close()
    conn.close()


def main():
    run_query("""
        SELECT uiu_id, full_name, email, phone
        FROM person
        WHERE designation = 'Student'
        ORDER BY uiu_id
        LIMIT 20
    """, "B1: All students")

    run_query("""
        SELECT route_code, route_name, service_type, distance_km
        FROM route
        WHERE is_active = TRUE
        ORDER BY service_type, route_code
    """, "B2: All active routes")

    run_query("""
        SELECT registration_no, shuttle_type, capacity, status
        FROM shuttle
        ORDER BY shuttle_id
    """, "B3: All shuttles")

    run_query("""
        SELECT stop_name, area
        FROM stop
        ORDER BY area, stop_name
        LIMIT 20
    """, "B4: All stops (first 20)")

    run_query("""
        SELECT uiu_id, full_name, email
        FROM person
        WHERE designation = 'Driver'
        ORDER BY uiu_id
    """, "B5: All drivers")


if __name__ == "__main__":
    main()