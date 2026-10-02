"""
main.py - University Shuttle Service Management System
Complete app: Student view + Admin CRUD + Card punch + Reports
"""
import sys
import os
import random
from datetime import date, datetime

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from db import get_connection


# ============================================================
# HELPERS
# ============================================================
def clear():
    os.system('cls' if os.name == 'nt' else 'clear')


def pause():
    input("\nPress Enter to continue...")


def header(title):
    print("\n" + "=" * 65)
    print(f"  {title}")
    print("=" * 65)


def query(sql, params=None, fetch=True):
    """Run a query. Returns list of dicts (or [] on error) when fetch=True,
    rowcount when fetch=False, or None on error for writes."""
    conn = get_connection()
    cur = conn.cursor(dictionary=True)
    try:
        cur.execute(sql, params or ())
        if fetch:
            return cur.fetchall()
        conn.commit()
        return cur.rowcount
    except Exception as e:
        conn.rollback()
        print(f"❌ DB Error: {e}")
        # FIX: return [] for reads so callers can safely iterate/len()
        return [] if fetch else None
    finally:
        cur.close()
        conn.close()


def run_insert(sql, params=None):
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(sql, params or ())
        conn.commit()
        return cur.lastrowid
    except Exception as e:
        conn.rollback()
        print(f"❌ Insert failed: {e}")
        return None
    finally:
        cur.close()
        conn.close()


def ask(prompt, default=None):
    val = input(prompt).strip()
    return val if val else default


# ============================================================
# STUDENT VIEW
# ============================================================
def student_view():
    header("STUDENT — CHECK MY BUS")

    uiu_id = ask("Enter your UIU ID (e.g., 011221001): ")
    if not uiu_id:
        return pause()

    student = query("""
        SELECT uiu_id, full_name, designation FROM person
        WHERE uiu_id = %s AND designation = 'Student'
    """, (uiu_id,))
    if not student:
        print(f"❌ No student found with UIU ID '{uiu_id}'.")
        return pause()

    s = student[0]
    print(f"\n👤 Welcome, {s['full_name']} ({s['uiu_id']})")

    regs = query("""
        SELECT sr.registration_id, r.route_id, r.route_code, r.route_name,
               t.term_name, sr.payment_status, sr.status,
               st.stop_name AS boarding_stop
        FROM student_registration sr
        JOIN route r ON sr.route_id = r.route_id
        JOIN term t ON sr.term_id = t.term_id
        LEFT JOIN stop st ON sr.boarding_stop_id = st.stop_id
        WHERE sr.student_uiu_id = %s
        ORDER BY sr.registration_date DESC
    """, (uiu_id,))

    if not regs:
        print("\n⚠️  You have no active registrations.")
        print("   Please contact the transport office.")
        return pause()

    print("\n📋 YOUR REGISTRATION:")
    for r in regs:
        print(f"   Route: {r['route_code']} — {r['route_name']}")
        print(f"   Term: {r['term_name']}")
        print(f"   Boarding stop: {r['boarding_stop'] or 'N/A'}")
        print(f"   Payment: {r['payment_status']}   Status: {r['status']}")

    paid_reg = next((r for r in regs
                     if r['payment_status'] == 'Paid' and r['status'] == 'Active'), None)
    if not paid_reg:
        print("\n⚠️  Payment not completed. Please complete payment to see buses.")
        return pause()

    route_id = paid_reg['route_id']

    trips = query("""
        SELECT t.trip_id, t.trip_date, t.passenger_count, t.status,
               s.departure_time, s.direction,
               sh.capacity, sh.registration_no
        FROM trip t
        JOIN schedule s ON t.schedule_id = s.schedule_id
        JOIN shuttle sh ON t.shuttle_id = sh.shuttle_id
        WHERE s.route_id = %s
          AND t.trip_date >= CURDATE()
          AND t.status <> 'Cancelled'
        ORDER BY t.trip_date, s.departure_time
        LIMIT 6
    """, (route_id,))

    print(f"\n🚌 NEXT BUSES FOR {paid_reg['route_code']}:")
    if not trips:
        print("   No upcoming trips scheduled.")
    else:
        for t in trips:
            cap = t['capacity']
            pax = t['passenger_count']
            pct = int((pax / cap) * 100) if cap > 0 else 0
            # FIX: clamp so pct > 100 doesn't produce a negative repeat count
            filled = min(pct // 10, 10)
            bar = "█" * filled + "░" * (10 - filled)
            status_note = ""
            if pct >= 100:
                status_note = " 🚨 FULL"
            elif pct >= 80:
                status_note = " ⚠️ Nearly full"

            print(f"   Trip {t['trip_id']:>4d} | {t['trip_date']} | "
                  f"{t['departure_time']} | {t['direction']}")
            print(f"      [{bar}] {pax}/{cap}{status_note}")

    return pause()


# ============================================================
# CRUD: PEOPLE
# ============================================================
def manage_people():
    while True:
        header("MANAGE PEOPLE")
        print("  1. Add new person")
        print("  2. View all persons")
        print("  3. Search person by UIU ID")
        print("  4. Update person")
        print("  5. Delete person")
        print("  0. Back")

        c = ask("\nChoose: ")

        if c == '1':
            uiu = ask("UIU ID: ")
            name = ask("Full name: ")
            desig = ask("Designation (Student/Faculty/Staff/Driver/Admin): ")
            email = ask("Email: ")
            phone = ask("Phone: ")
            addr = ask("Address (optional): ")

            run_insert("""
                INSERT INTO person
                    (uiu_id, full_name, designation, email, phone, address)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (uiu, name, desig, email, phone, addr))

            check = query("SELECT 1 FROM person WHERE uiu_id = %s", (uiu,))
            if check:
                print(f"\n✅ Person added: {name} ({uiu})")
            else:
                print(f"\n❌ Could not add person.")
            pause()

        elif c == '2':
            desig = ask("Filter by designation? (leave blank for all): ")
            if desig:
                rows = query("""
                    SELECT uiu_id, full_name, designation, email, phone
                    FROM person WHERE designation = %s
                    ORDER BY designation, uiu_id
                """, (desig,))
            else:
                rows = query("""
                    SELECT uiu_id, full_name, designation, email, phone
                    FROM person ORDER BY designation, uiu_id
                """)
            print(f"\n{'UIU ID':14s} {'Name':25s} {'Desig':10s} {'Email':28s} {'Phone':14s}")
            print("-" * 95)
            for r in rows:
                print(f"{r['uiu_id']:14s} {r['full_name'][:24]:25s} "
                      f"{r['designation']:10s} {(r['email'] or '')[:27]:28s} "
                      f"{r['phone'] or '':14s}")
            print(f"\nTotal: {len(rows)} person(s)")
            pause()

        elif c == '3':
            uiu = ask("UIU ID: ")
            row = query("SELECT * FROM person WHERE uiu_id = %s", (uiu,))
            if not row:
                print("❌ Not found.")
            else:
                for k, v in row[0].items():
                    print(f"   {k:15s}: {v}")
            pause()

        elif c == '4':
            uiu = ask("UIU ID to update: ")
            row = query("SELECT * FROM person WHERE uiu_id = %s", (uiu,))
            if not row:
                print("❌ Not found.")
                pause()
                continue
            r = row[0]
            print(f"\nCurrent name: {r['full_name']}")
            print(f"Current phone: {r['phone']}")
            print(f"Current email: {r['email']}")
            new_name = ask("New name (blank to keep): ")
            new_phone = ask("New phone (blank to keep): ")
            new_email = ask("New email (blank to keep): ")

            updates = []
            params = []
            if new_name:
                updates.append("full_name = %s"); params.append(new_name)
            if new_phone:
                updates.append("phone = %s"); params.append(new_phone)
            if new_email:
                updates.append("email = %s"); params.append(new_email)

            if updates:
                params.append(uiu)
                query(f"UPDATE person SET {', '.join(updates)} WHERE uiu_id = %s",
                      tuple(params), fetch=False)
                print("✅ Updated.")
            else:
                print("Nothing to update.")
            pause()

        elif c == '5':
            uiu = ask("UIU ID to delete: ")
            row = query("SELECT full_name FROM person WHERE uiu_id = %s", (uiu,))
            if not row:
                print("❌ Not found.")
                pause()
                continue
            print(f"\n⚠️  About to delete: {row[0]['full_name']} ({uiu})")
            if ask("Confirm? (yes/no): ").lower() == 'yes':
                query("DELETE FROM person WHERE uiu_id = %s", (uiu,), fetch=False)
                print("✅ Deleted.")
            else:
                print("Cancelled.")
            pause()

        elif c == '0':
            break
        else:
            print("❌ Invalid.")
            pause()


# ============================================================
# CRUD: ROUTES
# ============================================================
def manage_routes():
    while True:
        header("MANAGE ROUTES")
        print("  1. Add new route")
        print("  2. View all routes")
        print("  3. Update route")
        print("  4. Deactivate route")
        print("  5. Set route fee")
        print("  0. Back")

        c = ask("\nChoose: ")

        if c == '1':
            code = ask("Route code (e.g., Route-07): ")
            name = ask("Route name: ")
            stype = ask("Service type (ShortShuttle/RouteService/FacultyStaff): ")
            start_id = ask("Start stop ID (optional): ")
            end_id = ask("End stop ID (optional): ")
            km = ask("Distance km (optional): ")
            rem = ask("Remarks (optional): ")

            rid = run_insert("""
                INSERT INTO route
                    (route_code, route_name, service_type,
                     start_stop_id, end_stop_id, distance_km, remarks)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (code, name, stype,
                  int(start_id) if start_id else None,
                  int(end_id) if end_id else None,
                  float(km) if km else None,
                  rem))
            if rid:
                print(f"\n✅ Route added: {code} (ID: {rid})")
            pause()

        elif c == '2':
            rows = query("""
                SELECT route_id, route_code, route_name, service_type,
                       distance_km, is_active
                FROM route ORDER BY route_code
            """)
            print(f"\n{'ID':>3s} {'Code':12s} {'Name':35s} {'Service':15s} {'Km':>6s} {'Active':>7s}")
            print("-" * 90)
            for r in rows:
                print(f"{r['route_id']:>3d} {r['route_code']:12s} "
                      f"{r['route_name'][:34]:35s} {r['service_type']:15s} "
                      f"{str(r['distance_km'] or ''):>6s} {str(r['is_active']):>7s}")
            print(f"\nTotal: {len(rows)} route(s)")
            pause()

        elif c == '3':
            code = ask("Route code to update: ")
            row = query("SELECT * FROM route WHERE route_code = %s", (code,))
            if not row:
                print("❌ Not found.")
                pause()
                continue
            r = row[0]
            print(f"\nCurrent name: {r['route_name']}")
            print(f"Current remarks: {r['remarks']}")
            new_name = ask("New name (blank to keep): ")
            new_rem = ask("New remarks (blank to keep): ")

            updates, params = [], []
            if new_name:
                updates.append("route_name = %s"); params.append(new_name)
            if new_rem:
                updates.append("remarks = %s"); params.append(new_rem)

            if updates:
                params.append(code)
                query(f"UPDATE route SET {', '.join(updates)} WHERE route_code = %s",
                      tuple(params), fetch=False)
                print("✅ Updated.")
            else:
                print("Nothing to update.")
            pause()

        elif c == '4':
            code = ask("Route code to deactivate: ")
            query("UPDATE route SET is_active = FALSE WHERE route_code = %s",
                  (code,), fetch=False)
            print("✅ Route deactivated.")
            pause()

        elif c == '5':
            code = ask("Route code: ")
            row = query("SELECT route_id FROM route WHERE route_code = %s", (code,))
            if not row:
                print("❌ Not found.")
                pause()
                continue
            rid = row[0]['route_id']
            tri = ask("Trimester fee: ")
            sem = ask("Semester fee: ")
            # FIX: MySQL 8.0.20+ syntax — alias instead of deprecated VALUES()
            query("""
                INSERT INTO route_fee (route_id, term_type, fee_amount)
                VALUES (%s, 'Trimester', %s) AS new
                ON DUPLICATE KEY UPDATE fee_amount = new.fee_amount
            """, (rid, float(tri)), fetch=False)
            query("""
                INSERT INTO route_fee (route_id, term_type, fee_amount)
                VALUES (%s, 'Semester', %s) AS new
                ON DUPLICATE KEY UPDATE fee_amount = new.fee_amount
            """, (rid, float(sem)), fetch=False)
            print("✅ Fees updated.")
            pause()

        elif c == '0':
            break


# ============================================================
# CRUD: STOPS
# ============================================================
def manage_stops():
    while True:
        header("MANAGE STOPS")
        print("  1. Add new stop")
        print("  2. View all stops")
        print("  3. Delete stop")
        print("  0. Back")

        c = ask("\nChoose: ")

        if c == '1':
            name = ask("Stop name: ")
            area = ask("Area: ")
            lat = ask("Latitude (optional): ")
            lon = ask("Longitude (optional): ")
            sid = run_insert("""
                INSERT INTO stop (stop_name, area, latitude, longitude)
                VALUES (%s, %s, %s, %s)
            """, (name, area,
                  float(lat) if lat else None,
                  float(lon) if lon else None))
            if sid:
                print(f"✅ Stop added (ID: {sid})")
            pause()

        elif c == '2':
            rows = query("SELECT stop_id, stop_name, area FROM stop ORDER BY area, stop_name")
            print(f"\n{'ID':>3s} {'Stop Name':35s} {'Area':25s}")
            print("-" * 70)
            for r in rows:
                print(f"{r['stop_id']:>3d} {r['stop_name'][:34]:35s} {r['area'] or '':25s}")
            print(f"\nTotal: {len(rows)} stop(s)")
            pause()

        elif c == '3':
            sid = ask("Stop ID to delete: ")
            if ask(f"Confirm delete stop {sid}? (yes/no): ").lower() == 'yes':
                query("DELETE FROM stop WHERE stop_id = %s", (int(sid),), fetch=False)
                print("✅ Deleted (if not referenced by routes).")
            pause()

        elif c == '0':
            break


# ============================================================
# CRUD: SHUTTLES
# ============================================================
def manage_shuttles():
    while True:
        header("MANAGE SHUTTLES")
        print("  1. Add new shuttle")
        print("  2. View all shuttles")
        print("  3. Update shuttle status")
        print("  0. Back")

        c = ask("\nChoose: ")

        if c == '1':
            reg = ask("Registration number (bus plate): ")
            stype = ask("Type (Bus/Minibus/Microbus): ")
            cap = ask("Capacity: ")
            svc = ask("Service type (RouteService/ShortShuttle/FacultyStaff): ")
            sid = run_insert("""
                INSERT INTO shuttle
                    (registration_no, shuttle_type, capacity, service_type)
                VALUES (%s, %s, %s, %s)
            """, (reg, stype, int(cap), svc))
            if sid:
                print(f"✅ Shuttle added (ID: {sid})")
            pause()

        elif c == '2':
            rows = query("""
                SELECT shuttle_id, registration_no, shuttle_type,
                       capacity, service_type, status
                FROM shuttle ORDER BY shuttle_id
            """)
            print(f"\n{'ID':>3s} {'Reg No':26s} {'Type':10s} {'Cap':>5s} {'Service':15s} {'Status':12s}")
            print("-" * 80)
            for r in rows:
                print(f"{r['shuttle_id']:>3d} {r['registration_no']:26s} "
                      f"{r['shuttle_type']:10s} {r['capacity']:>5d} "
                      f"{r['service_type']:15s} {r['status']:12s}")
            pause()

        elif c == '3':
            sid = ask("Shuttle ID: ")
            st = ask("New status (Active/Maintenance/Retired): ")
            query("UPDATE shuttle SET status = %s WHERE shuttle_id = %s",
                  (st, int(sid)), fetch=False)
            print("✅ Updated.")
            pause()

        elif c == '0':
            break


# ============================================================
# REGISTRATION
# ============================================================
def register_student():
    header("REGISTER A STUDENT")

    uiu = ask("Enter Student UIU ID: ")
    if not uiu:
        return pause()

    existing = query("""
        SELECT uiu_id, full_name FROM person
        WHERE uiu_id = %s AND designation = 'Student'
    """, (uiu,))

    if existing:
        student = existing[0]
        print(f"\n👤 Existing student: {student['full_name']}")
        if ask("Continue with this student? (y/n): ").lower() != 'y':
            print("Cancelled.")
            return pause()
    else:
        print(f"\n🆕 New student — creating account for UIU ID: {uiu}")
        name = ask("Full name: ")
        email = ask("Email: ")
        phone = ask("Phone: ")
        address = ask("Address (optional): ")

        if not name or not email:
            print("❌ Name and email are required.")
            return pause()

        run_insert("""
            INSERT INTO person
                (uiu_id, full_name, designation, email, phone, address)
            VALUES (%s, %s, 'Student', %s, %s, %s)
        """, (uiu, name, email, phone, address))

        check = query("SELECT 1 FROM person WHERE uiu_id = %s", (uiu,))
        if not check:
            print("❌ Could not create student.")
            return pause()
        print(f"\n✅ New student account created: {name}")

    # STEP 1: term type
    print("\n📅 Which term are you registering for?")
    print("   1. Trimester  (shorter, cheaper fee)")
    print("   2. Semester   (longer, higher fee)")

    tchoice = ask("Choose (1/2): ")
    if tchoice not in ('1', '2'):
        print("❌ Invalid choice.")
        return pause()

    term_type = 'Trimester' if tchoice == '1' else 'Semester'

    term = query("""
        SELECT term_id, term_name, term_type FROM term
        WHERE term_type = %s
        ORDER BY start_date DESC LIMIT 1
    """, (term_type,))
    if not term:
        print(f"❌ No {term_type} term defined in the system.")
        return pause()
    term = term[0]
    print(f"\n📅 Using term: {term['term_name']} ({term['term_type']})")

    # STEP 2: route
    routes = query("""
        SELECT route_id, route_code, route_name FROM route
        WHERE service_type = 'RouteService' AND is_active = TRUE
        ORDER BY route_code
    """)
    print("\n📋 Paid Routes:")
    for r in routes:
        print(f"   [{r['route_id']:2d}] {r['route_code']:10s} {r['route_name']}")

    rid = ask("\nRoute ID: ")
    if not rid:
        return pause()
    rid = int(rid)

    dup = query("""
        SELECT 1 FROM student_registration
        WHERE student_uiu_id = %s AND route_id = %s AND term_id = %s
    """, (uiu, rid, term['term_id']))
    if dup:
        print(f"❌ Already registered for this route in {term['term_name']}.")
        return pause()

    # STEP 3: fee
    fee = query("""
        SELECT fee_amount FROM route_fee
        WHERE route_id = %s AND term_type = %s
    """, (rid, term['term_type']))
    if not fee:
        print(f"❌ No fee defined for this route for {term['term_type']}.")
        return pause()
    fee_amount = fee[0]['fee_amount']
    print(f"\n💰 Fee for {term['term_type']} students: {fee_amount} BDT")

    other = query("""
        SELECT fee_amount FROM route_fee
        WHERE route_id = %s AND term_type = %s
    """, (rid, 'Semester' if term['term_type'] == 'Trimester' else 'Trimester'))
    if other:
        other_type = 'Semester' if term['term_type'] == 'Trimester' else 'Trimester'
        print(f"   (For comparison — {other_type} fee: {other[0]['fee_amount']} BDT)")

    # STEP 4: boarding stop
    stops = query("""
        SELECT rs.stop_id, s.stop_name
        FROM route_stop rs
        JOIN stop s ON rs.stop_id = s.stop_id
        WHERE rs.route_id = %s AND rs.direction = 'INBOUND'
        ORDER BY rs.stop_order
    """, (rid,))
    print("\n🚏 Boarding Stops:")
    for s in stops:
        print(f"   [{s['stop_id']:2d}] {s['stop_name']}")
    stop_id = ask("\nStop ID: ")
    if not stop_id:
        return pause()

    # STEP 5: create registration
    reg_id = run_insert("""
        INSERT INTO student_registration
            (student_uiu_id, route_id, term_id, boarding_stop_id,
             fee_charged, payment_status, status)
        VALUES (%s, %s, %s, %s, %s, 'Pending', 'Active')
    """, (uiu, rid, term['term_id'], int(stop_id), fee_amount))

    # FIX: only trust reg_id; don't parse the SELECT 1 result for an ID
    if reg_id:
        print(f"\n✅ Registration created (ID: {reg_id})")
        print(f"   Term: {term['term_name']} ({term['term_type']})")
        print(f"   Fee charged: {fee_amount} BDT")
        print(f"   Payment status: Pending")
        print(f"   → Use option 8 to process payment.")
    else:
        print("❌ Registration failed.")
    pause()


def process_payment():
    header("PROCESS PAYMENT")

    pending = query("""
        SELECT sr.registration_id, sr.fee_charged,
               p.full_name, r.route_code
        FROM student_registration sr
        JOIN person p ON sr.student_uiu_id = p.uiu_id
        JOIN route r ON sr.route_id = r.route_id
        WHERE sr.payment_status = 'Pending'
        ORDER BY sr.registration_id DESC
        LIMIT 15
    """)
    if not pending:
        print("\n✅ No pending payments.")
        return pause()

    print("\n⏳ Pending Payments:")
    for p in pending:
        print(f"   [{p['registration_id']:3d}] {p['full_name'][:24]:25s} "
              f"{p['route_code']:10s} {p['fee_charged']:>7} BDT")

    rid = ask("\nRegistration ID to pay: ")
    if not rid:
        return pause()

    reg = query("""
        SELECT sr.fee_charged, sr.payment_status, p.full_name
        FROM student_registration sr
        JOIN person p ON sr.student_uiu_id = p.uiu_id
        WHERE sr.registration_id = %s
    """, (int(rid),))
    if not reg:
        print("❌ Not found.")
        return pause()
    reg = reg[0]

    print(f"\n👤 {reg['full_name']} — Amount: {reg['fee_charged']} BDT")

    if ask("Proceed with payment? (y/n): ").lower() != 'y':
        print("Cancelled.")
        return pause()

    print("\n🔄 Contacting payment gateway...")
    if random.random() < 0.95:
        txn = f"TXN-{random.randint(100000, 999999)}"
        query("""
            UPDATE student_registration
            SET payment_status = 'Paid', payment_date = CURDATE()
            WHERE registration_id = %s
        """, (int(rid),), fetch=False)
        print(f"✅ Payment successful! Txn: {txn}")
    else:
        print("❌ Payment failed.")
    pause()


def view_registrations():
    header("ALL REGISTRATIONS")

    rows = query("""
        SELECT sr.registration_id, p.full_name, p.uiu_id,
               r.route_code, t.term_name, sr.fee_charged,
               sr.payment_status, sr.status
        FROM student_registration sr
        JOIN person p ON sr.student_uiu_id = p.uiu_id
        JOIN route r ON sr.route_id = r.route_id
        JOIN term t ON sr.term_id = t.term_id
        ORDER BY sr.registration_date DESC
        LIMIT 30
    """)

    print(f"\n{'ID':>3s} {'Student':22s} {'UIU ID':12s} {'Route':10s} "
          f"{'Term':13s} {'Fee':>7s} {'Pay':8s} {'Status':10s}")
    print("-" * 100)
    for r in rows:
        print(f"{r['registration_id']:>3d} {r['full_name'][:21]:22s} "
              f"{r['uiu_id']:12s} {r['route_code']:10s} {r['term_name']:13s} "
              f"{r['fee_charged']:>7.0f} {r['payment_status']:8s} {r['status']:10s}")
    pause()


# ============================================================
# CARD PUNCH (Boarding)
# ============================================================
def card_punch():
    header("CARD PUNCH MACHINE — SIMULATE BOARDING")

    uiu = ask("Tap card (enter UIU ID): ")
    person = query("SELECT uiu_id, full_name, designation FROM person WHERE uiu_id = %s", (uiu,))
    if not person:
        print("❌ Card not recognized.")
        return pause()
    p = person[0]
    print(f"\n👤 {p['full_name']} ({p['designation']})")

    trips = query("""
        SELECT t.trip_id, r.route_code, s.direction, s.departure_time,
               sh.capacity, sh.registration_no, t.passenger_count
        FROM trip t
        JOIN schedule s ON t.schedule_id = s.schedule_id
        JOIN route r ON s.route_id = r.route_id
        JOIN shuttle sh ON t.shuttle_id = sh.shuttle_id
        WHERE t.trip_date = (SELECT MAX(trip_date) FROM trip)
          AND t.status <> 'Cancelled'
        ORDER BY t.trip_id
        LIMIT 12
    """)
    if not trips:
        print("❌ No trips available.")
        return pause()

    print("\n🚌 Available Trips (latest date):")
    for t in trips:
        print(f"   [{t['trip_id']:4d}] {t['route_code']:10s} {t['direction']:9s} "
              f"| {t['passenger_count']:2d}/{t['capacity']} | Bus {t['registration_no']}")

    trip_id = ask("\nEnter Trip ID: ")
    if not trip_id:
        return pause()
    trip_id = int(trip_id)

    trip = query("""
        SELECT t.trip_id, t.passenger_count, sh.capacity,
               r.service_type, r.route_id, s.direction
        FROM trip t
        JOIN schedule s ON t.schedule_id = s.schedule_id
        JOIN route r ON s.route_id = r.route_id
        JOIN shuttle sh ON t.shuttle_id = sh.shuttle_id
        WHERE t.trip_id = %s
    """, (trip_id,))
    if not trip:
        print("❌ Trip not found.")
        return pause()
    trip = trip[0]

    # FIX: block boarding a trip that's already full
    if trip['passenger_count'] >= trip['capacity']:
        print("🚨 Trip is already full. Cannot board.")
        return pause()

    already = query("""
        SELECT 1 FROM trip_passenger
        WHERE trip_id = %s AND person_uiu_id = %s
    """, (trip_id, uiu))
    if already:
        print("⚠️  Already boarded this trip.")
        return pause()

    boarding_type = "WalkOn"
    if trip['service_type'] == 'ShortShuttle':
        boarding_type = "Free"
    elif trip['service_type'] == 'FacultyStaff':
        auth = query("""
            SELECT 1 FROM faculty_authorization
            WHERE person_uiu_id = %s AND route_id = %s AND is_active = TRUE
        """, (uiu, trip['route_id']))
        if not auth:
            print("❌ Not authorized for faculty bus.")
            return pause()
        boarding_type = "Free"
    elif trip['service_type'] == 'RouteService':
        reg = query("""
            SELECT 1 FROM student_registration
            WHERE student_uiu_id = %s AND route_id = %s
              AND status = 'Active' AND payment_status = 'Paid'
        """, (uiu, trip['route_id']))
        boarding_type = "Registered" if reg else "WalkOn"

    stop = query("""
        SELECT stop_id FROM route_stop
        WHERE route_id = %s AND direction = %s
        ORDER BY stop_order LIMIT 1
    """, (trip['route_id'], trip['direction']))
    if not stop:
        print("❌ No stops configured for this route.")
        return pause()

    ok = run_insert("""
        INSERT INTO trip_passenger
            (trip_id, person_uiu_id, stop_id, boarding_type)
        VALUES (%s, %s, %s, %s)
    """, (trip_id, uiu, stop[0]['stop_id'], boarding_type))

    if not ok:
        print("❌ Boarding failed.")
        return pause()

    print(f"\n✅ Card accepted — boarded!")
    print(f"   Boarding type: {boarding_type}")

    upd = query("""
        SELECT passenger_count, status, departure_signal_sent
        FROM trip WHERE trip_id = %s
    """, (trip_id,))[0]

    print(f"   Onboard: {upd['passenger_count']}/{trip['capacity']}")
    if upd['departure_signal_sent']:
        print(f"   🚨 BUS IS FULL — driver notified to depart!")
    else:
        print(f"   Remaining seats: {trip['capacity'] - upd['passenger_count']}")
    pause()


# ============================================================
# REPORTS
# ============================================================
def report_revenue():
    header("REVENUE PER ROUTE")

    rows = query("""
        SELECT r.route_code, r.route_name,
               COUNT(sr.registration_id) AS students,
               COALESCE(SUM(sr.fee_charged), 0) AS revenue
        FROM route r
        LEFT JOIN student_registration sr
               ON r.route_id = sr.route_id AND sr.payment_status = 'Paid'
        WHERE r.service_type = 'RouteService'
        GROUP BY r.route_id, r.route_code, r.route_name
        ORDER BY revenue DESC
    """)

    total = 0
    print(f"\n{'Route':10s} {'Students':>10s} {'Revenue (BDT)':>16s}")
    print("-" * 42)
    for r in rows:
        print(f"{r['route_code']:10s} {r['students']:>10d} {r['revenue']:>16,.0f}")
        total += r['revenue']
    print("-" * 42)
    print(f"{'TOTAL':10s} {'':>10s} {total:>16,.0f}")
    pause()


def report_overcrowded():
    header("OVERCROWDED TRIPS (Passengers > Capacity)")

    rows = query("""
        SELECT t.trip_id, t.trip_date, r.route_code,
               t.passenger_count, sh.capacity
        FROM trip t
        JOIN schedule s ON t.schedule_id = s.schedule_id
        JOIN route r ON s.route_id = r.route_id
        JOIN shuttle sh ON t.shuttle_id = sh.shuttle_id
        WHERE t.passenger_count > sh.capacity
        ORDER BY t.trip_date DESC
        LIMIT 20
    """)
    if not rows:
        print("\n✅ No overcrowded trips found.")
        return pause()

    print(f"\n{'Trip':>6s} {'Date':12s} {'Route':10s} {'Pax':>5s} {'Cap':>5s}")
    print("-" * 45)
    for r in rows:
        print(f"{r['trip_id']:>6d} {str(r['trip_date']):12s} "
              f"{r['route_code']:10s} {r['passenger_count']:>5d} {r['capacity']:>5d}")
    pause()


def report_never_boarded():
    header("PAID BUT NEVER BOARDED")

    # FIX: scope "never boarded" to the specific route the student paid for,
    # not "ever boarded any trip anywhere".
    rows = query("""
        SELECT p.uiu_id, p.full_name, r.route_code, sr.fee_charged
        FROM student_registration sr
        JOIN person p ON sr.student_uiu_id = p.uiu_id
        JOIN route r ON sr.route_id = r.route_id
        WHERE sr.status = 'Active'
          AND sr.payment_status = 'Paid'
          AND NOT EXISTS (
              SELECT 1 FROM trip_passenger tp
              JOIN trip t     ON tp.trip_id = t.trip_id
              JOIN schedule sc ON t.schedule_id = sc.schedule_id
              WHERE tp.person_uiu_id = sr.student_uiu_id
                AND sc.route_id = sr.route_id
          )
        ORDER BY sr.fee_charged DESC
    """)
    if not rows:
        print("\n✅ Every paid student has boarded at least once.")
        return pause()

    print(f"\n{'UIU ID':12s} {'Name':26s} {'Route':10s} {'Paid':>8s}")
    print("-" * 62)
    for r in rows:
        print(f"{r['uiu_id']:12s} {r['full_name'][:25]:26s} "
              f"{r['route_code']:10s} {r['fee_charged']:>8.0f}")
    total = sum(r['fee_charged'] for r in rows)
    print("-" * 62)
    print(f"Unused revenue: {total:,.0f} BDT")
    pause()


def report_delay():
    header("DELAY ANALYSIS BY ROUTE")

    rows = query("""
        SELECT r.route_code,
               COUNT(*) AS trips,
               ROUND(AVG(TIME_TO_SEC(TIMEDIFF(TIME(t.actual_departure),
                                              s.departure_time))) / 60, 1) AS avg_delay,
               MAX(TIME_TO_SEC(TIMEDIFF(TIME(t.actual_departure),
                                        s.departure_time)) / 60) AS max_delay
        FROM trip t
        JOIN schedule s ON t.schedule_id = s.schedule_id
        JOIN route r ON s.route_id = r.route_id
        WHERE t.actual_departure IS NOT NULL
          AND t.status <> 'Cancelled'
        GROUP BY r.route_id, r.route_code
        ORDER BY avg_delay DESC
    """)

    print(f"\n{'Route':10s} {'Trips':>8s} {'Avg Delay':>12s} {'Max Delay':>12s}")
    print("-" * 48)
    for r in rows:
        print(f"{r['route_code']:10s} {r['trips']:>8d} "
              f"{float(r['avg_delay'] or 0):>10.1f}m "
              f"{float(r['max_delay'] or 0):>10.0f}m")
    pause()


def report_complaints():
    header("COMPLAINTS SUMMARY")

    print("\n📊 By Category:")
    rows = query("""
        SELECT category,
               COUNT(*) AS cnt,
               SUM(CASE WHEN status = 'Resolved' THEN 1 ELSE 0 END) AS resolved
        FROM complaint
        GROUP BY category
        ORDER BY cnt DESC
    """)
    print(f"{'Category':15s} {'Total':>8s} {'Resolved':>10s}")
    print("-" * 35)
    for r in rows:
        cnt = int(r['cnt'])
        resolved = int(r['resolved'] or 0)
        print(f"{r['category']:15s} {cnt:>8d} {resolved:>10d}")

    print("\n📊 By Status:")
    rows = query("SELECT status, COUNT(*) AS cnt FROM complaint GROUP BY status")
    for r in rows:
        print(f"   {r['status']:12s} {int(r['cnt']):>3d}")
    pause()


# ============================================================
# STUDENT FEEDBACK
# ============================================================
def submit_feedback():
    header("SUBMIT TRIP FEEDBACK")

    uiu = ask("Enter your UIU ID: ")
    person = query("SELECT uiu_id, full_name FROM person WHERE uiu_id = %s", (uiu,))
    if not person:
        print("❌ Person not found.")
        return pause()
    print(f"\n👤 {person[0]['full_name']}")

    trips = query("""
        SELECT t.trip_id, r.route_code, t.trip_date,
               s.departure_time, f.feedback_id
        FROM trip_passenger tp
        JOIN trip t ON tp.trip_id = t.trip_id
        JOIN schedule s ON t.schedule_id = s.schedule_id
        JOIN route r ON s.route_id = r.route_id
        LEFT JOIN feedback f ON f.trip_id = t.trip_id AND f.person_uiu_id = %s
        WHERE tp.person_uiu_id = %s
        ORDER BY t.trip_date DESC
        LIMIT 15
    """, (uiu, uiu))

    if not trips:
        print("\n⚠️  You haven't boarded any trips yet.")
        return pause()

    print("\n🚌 Your recent trips:")
    print(f"{'Trip':>6s} {'Route':10s} {'Date':12s} {'Time':9s} {'Feedback':>10s}")
    print("-" * 55)
    for t in trips:
        has_fb = "✅ Done" if t['feedback_id'] else "— none"
        print(f"{t['trip_id']:>6d} {t['route_code']:10s} {str(t['trip_date']):12s} "
              f"{str(t['departure_time']):9s} {has_fb:>10s}")

    trip_id = ask("\nEnter Trip ID to rate (or blank to cancel): ")
    if not trip_id:
        return pause()

    existing = query("""
        SELECT 1 FROM feedback
        WHERE person_uiu_id = %s AND trip_id = %s
    """, (uiu, int(trip_id)))
    if existing:
        print("⚠️  You already gave feedback for this trip.")
        return pause()

    print("\n⭐ Rate this trip (1=poor, 5=excellent):")
    print("   1 ⭐")
    print("   2 ⭐⭐")
    print("   3 ⭐⭐⭐")
    print("   4 ⭐⭐⭐⭐")
    print("   5 ⭐⭐⭐⭐⭐")

    try:
        rating = int(ask("Rating (1-5): "))
        if rating < 1 or rating > 5:
            print("❌ Rating must be between 1 and 5.")
            return pause()
    except ValueError:
        print("❌ Invalid rating.")
        return pause()

    comment = ask("Comment (optional, press Enter to skip): ")

    fb_id = run_insert("""
        INSERT INTO feedback (person_uiu_id, trip_id, rating, comment)
        VALUES (%s, %s, %s, %s)
    """, (uiu, int(trip_id), rating, comment or None))

    if fb_id:
        print(f"\n✅ Thank you for your feedback! (ID: {fb_id})")
        print(f"   Rating: {'⭐' * rating}")
    pause()


def report_feedback():
    header("FEEDBACK ANALYSIS")

    print("\n📊 Distribution by Rating:")
    rows = query("""
        SELECT rating, COUNT(*) AS cnt
        FROM feedback
        GROUP BY rating
        ORDER BY rating DESC
    """)
    print(f"{'Rating':10s} {'Count':>8s}")
    print("-" * 22)
    total = 0
    for r in rows:
        stars = "⭐" * int(r['rating'])
        print(f"{stars:10s} {int(r['cnt']):>8d}")
        total += r['cnt']
    print("-" * 22)
    print(f"{'Total':10s} {total:>8d}")

    avg = query("SELECT ROUND(AVG(rating), 2) AS avg_rating FROM feedback")
    if avg and avg[0]['avg_rating']:
        print(f"\n⭐ Overall average: {avg[0]['avg_rating']} / 5.00")

    print("\n📊 Average Rating by Route:")
    rows = query("""
        SELECT r.route_code,
               ROUND(AVG(f.rating), 2) AS avg_rating,
               COUNT(*) AS feedbacks
        FROM feedback f
        JOIN trip t ON f.trip_id = t.trip_id
        JOIN schedule s ON t.schedule_id = s.schedule_id
        JOIN route r ON s.route_id = r.route_id
        GROUP BY r.route_code
        ORDER BY avg_rating DESC
    """)
    print(f"{'Route':10s} {'Avg Rating':>12s} {'Feedbacks':>10s}")
    print("-" * 36)
    for r in rows:
        print(f"{r['route_code']:10s} {float(r['avg_rating']):>12.2f} {int(r['feedbacks']):>10d}")

    print("\n📝 Recent Comments:")
    rows = query("""
        SELECT p.full_name, f.rating, f.comment, t.trip_date, r.route_code
        FROM feedback f
        JOIN person p ON f.person_uiu_id = p.uiu_id
        JOIN trip t ON f.trip_id = t.trip_id
        JOIN schedule s ON t.schedule_id = s.schedule_id
        JOIN route r ON s.route_id = r.route_id
        WHERE f.comment IS NOT NULL
        ORDER BY f.created_at DESC
        LIMIT 8
    """)
    if not rows:
        print("   (no comments yet)")
    for r in rows:
        print(f"\n   ⭐{'⭐' * (int(r['rating']) - 1)} — {r['full_name']} on {r['route_code']}")
        print(f"      \"{r['comment']}\"")

    pause()


# ============================================================
# MANAGE SCHEDULES
# ============================================================
def manage_schedules():
    while True:
        header("MANAGE SCHEDULES")
        print("  1. Add new schedule")
        print("  2. View all schedules")
        print("  0. Back")

        c = ask("\nChoose: ")

        if c == '1':
            rid = ask("Route ID: ")
            sid = ask("Shuttle ID: ")
            drv = ask("Driver UIU ID: ")
            tid = ask("Term ID: ")
            direction = ask("Direction (INBOUND/OUTBOUND): ")
            dep = ask("Departure time (HH:MM:SS): ")
            arr = ask("Arrival time (HH:MM:SS): ")

            new_id = run_insert("""
                INSERT INTO schedule
                    (route_id, shuttle_id, driver_uiu_id, term_id,
                     direction, departure_time, arrival_time, operating_days)
                VALUES (%s, %s, %s, %s, %s, %s, %s, 'Mon-Fri')
            """, (int(rid), int(sid), drv, int(tid), direction, dep, arr))
            if new_id:
                print(f"✅ Schedule added (ID: {new_id})")
            pause()

        elif c == '2':
            rows = query("""
                SELECT s.schedule_id, r.route_code, sh.registration_no,
                       s.driver_uiu_id, s.direction, s.departure_time, s.arrival_time
                FROM schedule s
                JOIN route r ON s.route_id = r.route_id
                JOIN shuttle sh ON s.shuttle_id = sh.shuttle_id
                ORDER BY r.route_code, s.departure_time
            """)
            print(f"\n{'ID':>3s} {'Route':10s} {'Bus':24s} {'Driver':13s} "
                  f"{'Dir':9s} {'Dep':9s} {'Arr':9s}")
            print("-" * 90)
            for r in rows:
                print(f"{r['schedule_id']:>3d} {r['route_code']:10s} "
                      f"{r['registration_no']:24s} {r['driver_uiu_id'] or '':13s} "
                      f"{r['direction']:9s} {str(r['departure_time']):9s} "
                      f"{str(r['arrival_time'] or ''):9s}")
            pause()

        elif c == '0':
            break


def authorize_faculty():
    header("AUTHORIZE FACULTY / STAFF FOR BUS")

    uiu = ask("Enter UIU ID: ")
    if not uiu:
        return pause()

    existing = query("""
        SELECT uiu_id, full_name, designation FROM person
        WHERE uiu_id = %s
    """, (uiu,))

    if existing:
        p = existing[0]
        if p['designation'] not in ('Faculty', 'Staff'):
            print(f"\n❌ '{uiu}' exists but is a {p['designation']}, not Faculty/Staff.")
            print(f"   Use 'Manage People' (option 2) to change designation first.")
            return pause()
        print(f"\n👤 Existing {p['designation']}: {p['full_name']}")
    else:
        print(f"\n🆕 New person — creating account for UIU ID: {uiu}")
        name = ask("Full name: ")
        role = ask("Designation (Faculty/Staff): ").strip().capitalize()
        email = ask("Email: ")
        phone = ask("Phone: ")
        address = ask("Address (optional): ")

        if not name or not email:
            print("❌ Name and email are required.")
            return pause()
        if role not in ('Faculty', 'Staff'):
            print("❌ Designation must be 'Faculty' or 'Staff'.")
            return pause()

        # FIX: only ONE insert (the original had a duplicate that always failed)
        run_insert("""
            INSERT INTO person
                (uiu_id, full_name, designation, email, phone, address)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (uiu, name, role, email, phone, address))

        check = query("SELECT 1 FROM person WHERE uiu_id = %s", (uiu,))
        if not check:
            print("❌ Could not create person.")
            return pause()
        print(f"\n✅ New {role} account created: {name}")

    routes = query("""
        SELECT route_id, route_code, route_name FROM route
        WHERE service_type = 'FacultyStaff' AND is_active = TRUE
        ORDER BY route_code
    """)
    if not routes:
        print("❌ No faculty/staff routes defined.")
        print("   Use 'Manage Routes' (option 3) to create one first.")
        return pause()

    print("\n🚌 Faculty/Staff Routes:")
    for r in routes:
        print(f"   [{r['route_id']:2d}] {r['route_code']:12s} {r['route_name']}")

    route_id = ask("\nRoute ID: ")
    if not route_id:
        return pause()

    dup = query("""
        SELECT 1 FROM faculty_authorization
        WHERE person_uiu_id = %s AND route_id = %s AND is_active = TRUE
    """, (uiu, int(route_id)))
    if dup:
        print("⚠️  Already authorized for this route.")
        return pause()

    auth_id = run_insert("""
        INSERT INTO faculty_authorization
            (person_uiu_id, route_id, authorized_from, is_active)
        VALUES (%s, %s, CURDATE(), TRUE)
    """, (uiu, int(route_id)))

    if auth_id:
        print(f"\n✅ Authorization complete!")
        print(f"   UIU: {uiu}")
        print(f"   Route: {next((r['route_code'] for r in routes if r['route_id'] == int(route_id)), route_id)}")
        print(f"   Auth ID: {auth_id}")
        print(f"\n   They can now board the faculty bus using option 10.")
    pause()


def view_faculty_authorizations():
    header("FACULTY/STAFF BUS AUTHORIZATIONS")

    rows = query("""
        SELECT fa.auth_id, p.uiu_id, p.full_name, p.designation,
               r.route_code, r.route_name,
               fa.authorized_from, fa.is_active
        FROM faculty_authorization fa
        JOIN person p ON fa.person_uiu_id = p.uiu_id
        JOIN route r ON fa.route_id = r.route_id
        ORDER BY fa.authorized_from DESC
    """)

    if not rows:
        print("\n⚠️  No faculty/staff authorizations yet.")
        return pause()

    print(f"\n{'ID':>3s} {'UIU ID':14s} {'Name':22s} {'Role':8s} "
          f"{'Route':12s} {'Since':12s} {'Active':>7s}")
    print("-" * 90)
    for r in rows:
        print(f"{r['auth_id']:>3d} {r['uiu_id']:14s} {r['full_name'][:21]:22s} "
              f"{r['designation']:8s} {r['route_code']:12s} "
              f"{str(r['authorized_from']):12s} {str(r['is_active']):>7s}")
    print(f"\nTotal: {len(rows)} authorization(s)")
    pause()


# ============================================================
# MAIN MENU
# ============================================================
def main_menu():
    while True:
        clear()
        print("=" * 65)
        print("   UNIVERSITY SHUTTLE SERVICE MANAGEMENT SYSTEM")
        print("=" * 65)
        print()
        print("  ─── STUDENT ───")
        print("   1. Check my bus (next trips, occupancy)")
        print("  16. Submit trip feedback")
        print()
        print("  ─── ADMIN: MASTER DATA ───")
        print("   2. Manage People")
        print("   3. Manage Routes")
        print("   4. Manage Stops")
        print("   5. Manage Shuttles")
        print("   6. Manage Schedules")
        print()
        print("  ─── ADMIN: REGISTRATION ───")
        print("   7. Register a student")
        print("   8. Process payment")
        print("   9. View all registrations")
        print("  18. Authorize faculty/staff for bus")
        print("  19. View faculty authorizations")
        print()
        print("  ─── CARD PUNCH ───")
        print("  10. Simulate card punch (board a bus)")
        print()
        print("  ─── REPORTS ───")
        print("  11. Revenue per route")
        print("  12. Overcrowded trips")
        print("  13. Paid but never boarded")
        print("  14. Delay analysis")
        print("  15. Complaints summary")
        print("  17. Feedback analysis")
        print()
        print("   0. Exit")
        print()

        c = ask("  Choose: ")

        if   c == '1':  student_view()
        elif c == '2':  manage_people()
        elif c == '3':  manage_routes()
        elif c == '4':  manage_stops()
        elif c == '5':  manage_shuttles()
        elif c == '6':  manage_schedules()
        elif c == '7':  register_student()
        elif c == '8':  process_payment()
        elif c == '9':  view_registrations()
        elif c == '10': card_punch()
        elif c == '11': report_revenue()
        elif c == '12': report_overcrowded()
        elif c == '13': report_never_boarded()
        elif c == '14': report_delay()
        elif c == '15': report_complaints()
        elif c == '16': submit_feedback()
        elif c == '17': report_feedback()
        elif c == '18': authorize_faculty()
        elif c == '19': view_faculty_authorizations()
        elif c == '0':
            print("\n👋 Goodbye!\n")
            break
        else:
            print("❌ Invalid option.")
            pause()


if __name__ == "__main__":
    main_menu()