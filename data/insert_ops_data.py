import sys
import os
from datetime import date, time, datetime, timedelta
import random

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from db import get_connection


def run(cur, sql, params=None):
    cur.execute(sql, params or ())
    return cur.lastrowid


def insert_trips(cur):
    print("🚍 Trips...")
    random.seed(42)

    cur.execute("""
        SELECT schedule_id, shuttle_id, driver_uiu_id
        FROM schedule
    """)
    schedules = cur.fetchall()

    start = date(2025, 1, 6)
    count = 0
    for week in range(4):
        for day_offset in range(5):  # Mon-Fri
            trip_date = start + timedelta(days=week * 7 + day_offset)
            for sched_id, shuttle_id, driver_uiu_id in schedules:
                r = random.random()
                if r < 0.03:
                    status = "Cancelled"
                    act_dep = act_arr = None
                    pcount = 0
                else:
                    delay = random.choice([0, 0, 0, 2, 3, 5, 8, 12, 15, 20])
                    status = "Completed"          # Delay is derived, not a status
                    act_dep = datetime.combine(trip_date, time(8, 0)) + timedelta(minutes=delay)
                    act_arr = act_dep + timedelta(minutes=70)
                    pcount = random.randint(5, 50)

                run(cur, """
                    INSERT INTO trip
                        (schedule_id, shuttle_id, driver_uiu_id, trip_date,
                         actual_departure, actual_arrival, passenger_count, status)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """, (sched_id, shuttle_id, driver_uiu_id, trip_date,
                      act_dep, act_arr, pcount, status))
                count += 1
    print(f"   ✅ Inserted {count} trips")


# ============================================================
# TRIP PASSENGERS (auto-inserted by card punch machine)
# ============================================================
def insert_trip_passengers(cur):
    print("🧍 Trip passengers...")
    random.seed(7)

    cur.execute("""
        SELECT student_uiu_id, route_id, boarding_stop_id
        FROM student_registration
        WHERE status = 'Active'
    """)
    regs = cur.fetchall()

    cur.execute("""
        SELECT t.trip_id, s.route_id
        FROM trip t
        JOIN schedule s ON t.schedule_id = s.schedule_id
        WHERE t.status <> 'Cancelled'
    """)
    trips = cur.fetchall()

    cur.execute("SELECT uiu_id FROM person WHERE designation = 'Student'")
    all_students = [r[0] for r in cur.fetchall()]

    count = 0
    for trip_id, route_id in trips:
        boarded = set()
        route_regs = [r for r in regs if r[1] == route_id]

        # Registered students on this route
        for uiu, _, stop_id in route_regs:
            if random.random() < 0.7:
                run(cur, """
                    INSERT INTO trip_passenger
                        (trip_id, person_uiu_id, stop_id, boarded_at, boarding_type)
                    VALUES (%s, %s, %s, %s, 'Registered')
                """, (trip_id, uiu, stop_id,
                      datetime.combine(date(2025, 1, 6), time(8, 0))))
                boarded.add(uiu)
                count += 1

        # Walk-ons (unregistered students)
        registered_ids = {r[0] for r in route_regs}
        candidates = [s for s in all_students
                      if s not in registered_ids and s not in boarded]

        if random.random() < 0.05 and candidates:
            walker = random.choice(candidates)
            cur.execute("SELECT stop_id FROM stop LIMIT 1")
            stop_id = cur.fetchone()[0]
            run(cur, """
                INSERT INTO trip_passenger
                    (trip_id, person_uiu_id, stop_id, boarded_at, boarding_type)
                VALUES (%s, %s, %s, %s, 'WalkOn')
            """, (trip_id, walker, stop_id,
                  datetime.combine(date(2025, 1, 6), time(8, 0))))
            count += 1

    print(f"   ✅ Inserted {count} passenger records")


# ============================================================
# COMPLAINTS
# ============================================================
def insert_complaints(cur):
    print("😠 Complaints...")
    random.seed(11)

    cur.execute("SELECT uiu_id FROM person WHERE designation = 'Student' LIMIT 10")
    students = [r[0] for r in cur.fetchall()]

    # Delayed trips = actual departure more than 5 min after scheduled
    cur.execute("""
        SELECT t.trip_id
        FROM trip t
        JOIN schedule s ON t.schedule_id = s.schedule_id
        WHERE t.actual_departure IS NOT NULL
          AND TIME(t.actual_departure) > ADDTIME(s.departure_time, '00:05:00')
        LIMIT 20
    """)
    delayed_trips = [r[0] for r in cur.fetchall()]

    cur.execute("SELECT route_id FROM route WHERE service_type = 'RouteService'")
    routes = [r[0] for r in cur.fetchall()]

    cur.execute("SELECT shuttle_id FROM shuttle LIMIT 5")
    shuttles = [r[0] for r in cur.fetchall()]

    categories = ["Delay", "Overcrowding", "Behavior", "Cleanliness", "Other"]
    descriptions = {
        "Delay": "Bus was significantly late this morning.",
        "Overcrowding": "Too many passengers, had to stand the whole way.",
        "Behavior": "Driver was rude and drove recklessly.",
        "Cleanliness": "Bus interior was not clean.",
        "Other": "General service concern.",
    }

    count = 0
    for _ in range(25):
        complainant = random.choice(students)
        category = random.choice(categories)

        trip_id = random.choice(delayed_trips) if delayed_trips and random.random() < 0.6 else None
        route_id = random.choice(routes) if random.random() < 0.7 else None
        shuttle_id = random.choice(shuttles) if random.random() < 0.5 else None

        if not (trip_id or route_id or shuttle_id):
            route_id = random.choice(routes)

        status = random.choice(["Open", "InProgress", "Resolved"])
        cdate = date(2025, 1, 6) + timedelta(days=random.randint(0, 25))

        run(cur, """
            INSERT INTO complaint
                (complainant_uiu_id, trip_id, route_id, shuttle_id,
                 complaint_date, category, description, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (complainant, trip_id, route_id, shuttle_id,
              cdate, category, descriptions[category], status))
        count += 1
    print(f"   ✅ Inserted {count} complaints")


# ============================================================
# MAINTENANCE
# ============================================================
def insert_maintenance(cur):
    print("🔧 Maintenance...")
    random.seed(21)

    cur.execute("SELECT shuttle_id FROM shuttle")
    shuttles = [r[0] for r in cur.fetchall()]
    types = ["Routine", "Repair", "Inspection"]
    workshops = ["UIU Workshop", "ABC Motors", "City Auto Care", "Dhaka Fleet"]

    count = 0
    for shuttle_id in shuttles:
        for _ in range(random.randint(1, 3)):
            mtype = random.choice(types)
            mdate = date(2025, 1, 10) + timedelta(days=random.randint(0, 60))
            cost = random.choice([1500, 2500, 3500, 4500, 6000, 8000, 12000])

            run(cur, """
                INSERT INTO maintenance
                    (shuttle_id, maintenance_date, maintenance_type,
                     description, cost, workshop_name, next_due_date)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (shuttle_id, mdate, mtype, f"{mtype} service performed.",
                  cost, random.choice(workshops), mdate + timedelta(days=60)))
            count += 1
    print(f"   ✅ Inserted {count} maintenance records")


# ============================================================
# MAIN
# ============================================================
def main():
    conn = get_connection()
    if not conn:
        print("❌ Cannot connect.")
        return
    cur = conn.cursor()
    try:
        print("🧹 Clearing existing operational data...")
        cur.execute("SET FOREIGN_KEY_CHECKS = 0")
        for t in ["trip_passenger", "complaint", "maintenance", "trip"]:
            cur.execute(f"DELETE FROM {t}")
        cur.execute("SET FOREIGN_KEY_CHECKS = 1")

        insert_trips(cur)
        insert_trip_passengers(cur)
        insert_complaints(cur)
        insert_maintenance(cur)

        conn.commit()
        print("\n✅ Operational data inserted successfully!")

        for t in ["trip", "trip_passenger", "complaint", "maintenance"]:
            cur.execute(f"SELECT COUNT(*) FROM {t}")
            print(f"   {t:20s} = {cur.fetchone()[0]}")
    except Exception as e:
        conn.rollback()
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        cur.close()
        conn.close()


if __name__ == "__main__":
    main()