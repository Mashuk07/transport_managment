"""
insert_reference_data.py - Master data for USSMS
Run this FIRST.
"""
import sys
import os
from datetime import date, timedelta

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from db import get_connection


def run(cur, sql, params=None):
    cur.execute(sql, params or ())
    return cur.lastrowid


# ============================================================
# TERMS + CALENDAR
# ============================================================
def insert_terms(cur):
    print("📅 Terms...")
    ids = []
    for name, ttype, s, e in [
        ("Spring 2025", "Trimester", "2025-01-05", "2025-04-20"),
        ("Summer 2025", "Semester",  "2025-05-10", "2025-09-15"),
    ]:
        ids.append(run(cur, """
            INSERT INTO term (term_name, term_type, start_date, end_date)
            VALUES (%s, %s, %s, %s)
        """, (name, ttype, s, e)))
    return ids


def insert_calendar(cur, term_ids):
    print("📆 Calendar (Fri+Sat off + holidays)...")
    start, end = date(2025, 1, 5), date(2025, 4, 20)
    special = {
        date(2025, 2, 21): "International Mother Language Day",
        date(2025, 3, 17): "Sheikh Mujib's Birthday",
        date(2025, 3, 26): "Independence Day",
        date(2025, 4, 14): "Pohela Boishakh",
    }
    exam_start, exam_end = date(2025, 4, 5), date(2025, 4, 15)

    d = start
    while d <= end:
        if d in special:
            dtype, rem = "OffDay", special[d]
        elif exam_start <= d <= exam_end:
            dtype, rem = "ExamDay", "Final exams"
        elif d.weekday() in (4, 5):  # Friday, Saturday
            dtype, rem = "OffDay", "Weekly holiday"
        else:
            dtype, rem = "ClassDay", None

        run(cur, """
            INSERT INTO term_calendar (term_id, calendar_date, day_type, remarks)
            VALUES (%s, %s, %s, %s)
        """, (term_ids[0], d, dtype, rem))
        d += timedelta(days=1)


# ============================================================
# STOPS
# ============================================================
def insert_stops(cur):
    print("🚏 Stops...")
    stops = [
        ("Zigatola Bus Stop", "Dhanmondi"),
        ("Dhanmondi Keari Plaza", "Dhanmondi"),
        ("Shankar Bus Stop", "Dhanmondi"),
        ("Mohammadpur BRTC", "Mohammadpur"),
        ("Manik Mia Avenue", "Sher-e-Bangla Nagar"),
        ("BARC Farmgate", "Farmgate"),
        ("Kakoli", "Banani"),
        ("Gulshan 2", "Gulshan"),
        ("Notun Bazar", "Gulshan"),
        ("UIU Main Campus", "Bashundhara"),
        ("Technical Mor", "Mirpur"),
        ("Mirpur 1", "Mirpur"),
        ("Mirpur 2", "Mirpur"),
        ("Mirpur 10", "Mirpur"),
        ("Mirpur 11", "Mirpur"),
        ("Mirpur 12", "Mirpur"),
        ("ECB Chattar (Kalshi)", "Mirpur"),
        ("Kuril Flyover", "Kuril"),
        ("Signboard Mor", "Narayanganj"),
        ("Hanif Flyover", "Jatrabari"),
        ("Manik Nagar", "Mugdapara"),
        ("Mugdapara", "Mugdapara"),
        ("Bashabo", "Bashabo"),
        ("Khilgaon Police Fari", "Khilgaon"),
        ("Abul Hotel", "Malibagh"),
        ("Rampura Bridge", "Rampura"),
        ("Aftab Nagar", "Aftab Nagar"),
        ("Sunvalley Showdesh", "Aftab Nagar"),
        ("Jatrabari Mor", "Jatrabari"),
        ("Palashi", "Azimpur"),
        ("Azimpur", "Azimpur"),
        ("Dhaka College", "Dhanmondi"),
        ("City College", "Dhanmondi"),
        ("West Kalabagan", "Dhanmondi"),
        ("Panthapath", "Dhanmondi"),
        ("Abdullahpur", "Uttara"),
        ("House Building", "Uttara"),
        ("Azampur", "Uttara"),
        ("Jashimuddin", "Uttara"),
        ("Airport", "Airport"),
        ("Khilkhet", "Khilkhet"),
        ("300 ft", "Bashundhara"),
        ("Bashundhara Gate", "Bashundhara"),
    ]
    ids = {}
    for name, area in stops:
        ids[name] = run(cur, "INSERT INTO stop (stop_name, area) VALUES (%s, %s)", (name, area))
    return ids


# ============================================================
# ROUTES + FEES + ROUTE_STOPS
# ============================================================
def insert_routes(cur, S):
    print("🛣️  Routes...")
    routes = [
        ("Route-01", "Zigatola – UIU via Farmgate/Gulshan", "RouteService",
         S["Zigatola Bus Stop"], S["UIU Main Campus"], 21.5,
         "No stoppage Farmgate->Kakoli; Elevated Expressway on return."),
        ("Route-03", "Technical – UIU via Mirpur/Kuril", "RouteService",
         S["Technical Mor"], S["UIU Main Campus"], 18.0, None),
        ("Route-04A", "Signboard Mor – UIU via Mugdapara", "RouteService",
         S["Signboard Mor"], S["UIU Main Campus"], 24.0, None),
        ("Route-04B", "Jatrabari Mor – UIU via Mugdapara", "RouteService",
         S["Jatrabari Mor"], S["UIU Main Campus"], 23.5, None),
        ("Route-05", "Palashi – UIU via Farmgate/Gulshan", "RouteService",
         S["Palashi"], S["UIU Main Campus"], 20.0,
         "No stoppage Farmgate->Kakoli."),
        ("Route-06", "Abdullahpur – UIU via Airport", "RouteService",
         S["Abdullahpur"], S["UIU Main Campus"], 15.0, None),
        ("Short-01", "UIU – Notun Bazar Shuttle", "ShortShuttle",
         S["UIU Main Campus"], S["Notun Bazar"], 5.0, "Free loop."),
        ("Short-02", "UIU – Aftab Nagar Shuttle", "ShortShuttle",
         S["UIU Main Campus"], S["Aftab Nagar"], 4.5, "Free loop."),
        ("Short-03", "UIU – Kuril Shuttle", "ShortShuttle",
         S["UIU Main Campus"], S["Kuril Flyover"], 3.0, "Free loop."),
        ("Faculty-01", "Faculty/Staff – UIU Shuttle", "FacultyStaff",
         S["UIU Main Campus"], S["Notun Bazar"], 4.0, "Faculty only."),
    ]
    ids = {}
    for code, name, stype, start, end, km, rem in routes:
        ids[code] = run(cur, """
            INSERT INTO route
                (route_code, route_name, service_type,
                 start_stop_id, end_stop_id, distance_km, remarks)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (code, name, stype, start, end, km, rem))
    return ids


def insert_route_stops(cur, R, S):
    print("🧭 Route stops...")

    def add(code, direction, stops, etas):
        for order, (sname, eta) in enumerate(zip(stops, etas), 1):
            run(cur, """
                INSERT INTO route_stop
                    (route_id, direction, stop_order, stop_id, eta_offset_min)
                VALUES (%s, %s, %s, %s, %s)
            """, (R[code], direction, order, S[sname], eta))

    add("Route-01", "INBOUND",
        ["Zigatola Bus Stop", "Dhanmondi Keari Plaza", "Shankar Bus Stop",
         "Mohammadpur BRTC", "Manik Mia Avenue", "BARC Farmgate", "Kakoli",
         "Gulshan 2", "Notun Bazar", "UIU Main Campus"],
        [0, 5, 9, 15, 22, 30, 38, 45, 55, 75])
    add("Route-01", "OUTBOUND",
        ["UIU Main Campus", "Notun Bazar", "Gulshan 2", "Manik Mia Avenue",
         "Mohammadpur BRTC", "Shankar Bus Stop", "Dhanmondi Keari Plaza",
         "Zigatola Bus Stop"],
        [0, 12, 22, 40, 50, 58, 63, 70])
    add("Route-03", "INBOUND",
        ["Technical Mor", "Mirpur 1", "Mirpur 2", "Mirpur 10", "Mirpur 11",
         "Mirpur 12", "ECB Chattar (Kalshi)", "Kuril Flyover",
         "Notun Bazar", "UIU Main Campus"],
        [0, 6, 12, 18, 24, 30, 38, 50, 60, 75])
    add("Route-03", "OUTBOUND",
        ["UIU Main Campus", "Notun Bazar", "Kuril Flyover", "ECB Chattar (Kalshi)",
         "Mirpur 12", "Mirpur 11", "Mirpur 10", "Mirpur 2", "Mirpur 1", "Technical Mor"],
        [0, 15, 25, 38, 46, 52, 58, 64, 70, 78])
    add("Route-04A", "INBOUND",
        ["Signboard Mor", "Hanif Flyover", "Manik Nagar", "Mugdapara",
         "Bashabo", "Khilgaon Police Fari", "Abul Hotel", "Rampura Bridge",
         "Aftab Nagar", "Sunvalley Showdesh", "UIU Main Campus"],
        [0, 10, 20, 28, 35, 42, 50, 58, 68, 75, 90])
    add("Route-04B", "INBOUND",
        ["Jatrabari Mor", "Manik Nagar", "Mugdapara", "Bashabo",
         "Khilgaon Police Fari", "Abul Hotel", "Rampura Bridge",
         "Aftab Nagar", "Sunvalley Showdesh", "UIU Main Campus"],
        [0, 12, 20, 28, 35, 42, 50, 60, 67, 82])
    add("Route-05", "INBOUND",
        ["Palashi", "Azimpur", "Dhaka College", "City College",
         "West Kalabagan", "Panthapath", "BARC Farmgate", "Kakoli",
         "Gulshan 2", "Notun Bazar", "UIU Main Campus"],
        [0, 5, 10, 15, 20, 25, 35, 42, 50, 60, 80])
    add("Route-05", "OUTBOUND",
        ["UIU Main Campus", "Notun Bazar", "Gulshan 2", "Panthapath",
         "West Kalabagan", "City College", "Dhaka College", "Azimpur", "Palashi"],
        [0, 14, 24, 45, 52, 58, 65, 72, 78])
    add("Route-06", "INBOUND",
        ["Abdullahpur", "House Building", "Azampur", "Jashimuddin",
         "Airport", "Khilkhet", "Kuril Flyover", "300 ft",
         "Bashundhara Gate", "UIU Main Campus"],
        [0, 5, 10, 15, 22, 30, 40, 48, 55, 65])
    add("Route-06", "OUTBOUND",
        ["UIU Main Campus", "Bashundhara Gate", "300 ft", "Kuril Flyover",
         "Khilkhet", "Airport", "Jashimuddin", "Azampur",
         "House Building", "Abdullahpur"],
        [0, 8, 15, 25, 35, 42, 48, 52, 57, 62])
    add("Short-01", "OUTBOUND", ["UIU Main Campus", "Notun Bazar"], [0, 12])
    add("Short-01", "INBOUND",  ["Notun Bazar", "UIU Main Campus"], [0, 12])
    add("Short-02", "OUTBOUND", ["UIU Main Campus", "Aftab Nagar"], [0, 10])
    add("Short-02", "INBOUND",  ["Aftab Nagar", "UIU Main Campus"], [0, 10])
    add("Short-03", "OUTBOUND", ["UIU Main Campus", "Kuril Flyover"], [0, 8])
    add("Short-03", "INBOUND",  ["Kuril Flyover", "UIU Main Campus"], [0, 8])
    add("Faculty-01", "OUTBOUND", ["UIU Main Campus", "Notun Bazar"], [0, 12])
    add("Faculty-01", "INBOUND",  ["Notun Bazar", "UIU Main Campus"], [0, 12])


def insert_route_fees(cur, R):
    print("💰 Route fees...")
    for code, tri, sem in [
        ("Route-01", 3000, 4500), ("Route-03", 3500, 5000),
        ("Route-04A", 3200, 4700), ("Route-04B", 3200, 4700),
        ("Route-05", 2800, 4200), ("Route-06", 2500, 3800),
        ("Short-01", 0, 0), ("Short-02", 0, 0), ("Short-03", 0, 0),
        ("Faculty-01", 0, 0),
    ]:
        run(cur, "INSERT INTO route_fee (route_id, term_type, fee_amount) VALUES (%s,'Trimester',%s)", (R[code], tri))
        run(cur, "INSERT INTO route_fee (route_id, term_type, fee_amount) VALUES (%s,'Semester',%s)",  (R[code], sem))


# ============================================================
# SHUTTLES
# ============================================================
def insert_shuttles(cur):
    print("🚌 Shuttles...")
    ids = []
    for reg, stype, cap, service, status in [
        ("DHAKA-METRO-BA-11-2345", "Bus",      52, "RouteService", "Active"),
        ("DHAKA-METRO-BA-11-2346", "Bus",      52, "RouteService", "Active"),
        ("DHAKA-METRO-BA-11-2347", "Bus",      52, "RouteService", "Active"),
        ("DHAKA-METRO-BA-11-2348", "Minibus",  32, "RouteService", "Active"),
        ("DHAKA-METRO-BA-11-2349", "Minibus",  32, "RouteService", "Maintenance"),
        ("DHAKA-METRO-BA-11-2350", "Microbus", 16, "ShortShuttle", "Active"),
        ("DHAKA-METRO-BA-11-2351", "Microbus", 16, "ShortShuttle", "Active"),
        ("DHAKA-METRO-BA-11-2352", "Bus",      45, "FacultyStaff", "Active"),
    ]:
        ids.append(run(cur, """
            INSERT INTO shuttle
                (registration_no, shuttle_type, capacity, service_type, status)
            VALUES (%s, %s, %s, %s, %s)
        """, (reg, stype, cap, service, status)))
    return ids


# ============================================================
# PERSONS
# ============================================================
def insert_persons(cur):
    print("🧑 Persons (unified with uiu_id)...")
    persons = [
        # Students (uiu_id, name, designation, email, phone)
        ("011221001", "Rahim Uddin",      "Student", "rahim@uiu.ac.bd",   "01711000001"),
        ("011221002", "Karima Akter",     "Student", "karima@uiu.ac.bd",  "01711000002"),
        ("011221003", "Sajid Hasan",      "Student", "sajid@uiu.ac.bd",   "01711000003"),
        ("011221004", "Nusrat Jahan",     "Student", "nusrat@uiu.ac.bd",  "01711000004"),
        ("011221005", "Tanvir Ahmed",     "Student", "tanvir@uiu.ac.bd",  "01711000005"),
        ("011222006", "Farhana Islam",    "Student", "farhana@uiu.ac.bd", "01711000006"),
        ("011222007", "Mehedi Hasan",     "Student", "mehedi@uiu.ac.bd",  "01711000007"),
        ("011223008", "Sadia Rahman",     "Student", "sadia@uiu.ac.bd",   "01711000008"),
        ("011223009", "Arif Chowdhury",   "Student", "arif@uiu.ac.bd",    "01711000009"),
        ("011223010", "Tasnim Akter",     "Student", "tasnim@uiu.ac.bd",  "01711000010"),
        ("011223011", "Imran Khan",       "Student", "imran@uiu.ac.bd",   "01711000011"),
        ("011223012", "Lubna Ferdous",    "Student", "lubna@uiu.ac.bd",   "01711000012"),
        ("011224013", "Rifat Hossain",    "Student", "rifat@uiu.ac.bd",   "01711000013"),
        ("011224014", "Sumaiya Islam",    "Student", "sumaiya@uiu.ac.bd", "01711000014"),
        ("011224015", "Nayeem Ahmed",     "Student", "nayeem@uiu.ac.bd",  "01711000015"),
        ("011224016", "Raisa Karim",      "Student", "raisa@uiu.ac.bd",   "01711000016"),
        ("011224017", "Shakib Al Hasan",  "Student", "shakib@uiu.ac.bd",  "01711000017"),
        ("011225018", "Mim Akter",        "Student", "mim@uiu.ac.bd",     "01711000018"),
        ("011225019", "Fahim Rahman",     "Student", "fahim@uiu.ac.bd",   "01711000019"),
        ("011225020", "Nabila Sultana",   "Student", "nabila@uiu.ac.bd",  "01711000020"),
        # Drivers
        ("01811000001", "Karim Mia",       "Driver", "karim.driver@uiu.ac.bd",   "01811000001"),
        ("01811000002", "Jamal Hossain",   "Driver", "jamal.driver@uiu.ac.bd",   "01811000002"),
        ("01811000003", "Rafiq Islam",     "Driver", "rafiq.driver@uiu.ac.bd",   "01811000003"),
        ("01811000004", "Sabbir Ahmed",    "Driver", "sabbir.driver@uiu.ac.bd",  "01811000004"),
        ("01811000005", "Mizanur Rahman",  "Driver", "mizan.driver@uiu.ac.bd",   "01811000005"),
        ("01811000006", "Alamgir Hossain", "Driver", "alamgir.driver@uiu.ac.bd", "01811000006"),
        # Admins
        ("01911000001", "Transport Admin",  "Admin", "admin.transport@uiu.ac.bd", "01911000001"),
        ("01911000002", "Registrar Office", "Admin", "registrar@uiu.ac.bd",       "01911000002"),
        # Faculty
        ("01611000001", "Dr. Ahmed Saleh",  "Faculty", "ahmed.saleh@uiu.ac.bd", "01611000001"),
        ("01611000002", "Prof. Nazma Ara",  "Faculty", "nazma.ara@uiu.ac.bd",   "01611000002"),
        # Staff
        ("01611000003", "Mr. Rafiq Uddin",  "Staff",   "rafiq.staff@uiu.ac.bd", "01611000003"),
    ]
    for uiu, name, desig, email, phone in persons:
        run(cur, """
            INSERT INTO person (uiu_id, full_name, designation, email, phone)
            VALUES (%s, %s, %s, %s, %s)
        """, (uiu, name, desig, email, phone))


# ============================================================
# SCHEDULES
# ============================================================
def insert_schedules(cur, R, term_ids, sh, drivers):
    print("🗓️  Schedules...")
    rows = [
        ("Route-01", "INBOUND", 0, drivers[0], "07:00:00", "08:15:00"),
        ("Route-01", "INBOUND", 1, drivers[1], "08:30:00", "09:45:00"),
        ("Route-01", "OUTBOUND", 0, drivers[0], "17:00:00", "18:10:00"),
        ("Route-03", "INBOUND", 2, drivers[2], "06:45:00", "08:00:00"),
        ("Route-03", "OUTBOUND", 2, drivers[2], "17:30:00", "18:45:00"),
        ("Route-04A", "INBOUND", 3, drivers[3], "06:30:00", "08:00:00"),
        ("Route-04A", "OUTBOUND", 3, drivers[3], "17:15:00", "18:45:00"),
        ("Route-04B", "INBOUND", 3, drivers[4], "06:45:00", "08:05:00"),
        ("Route-04B", "OUTBOUND", 3, drivers[4], "17:20:00", "18:40:00"),
        ("Route-05", "INBOUND", 4, drivers[5], "07:15:00", "08:35:00"),
        ("Route-05", "OUTBOUND", 4, drivers[5], "17:00:00", "18:20:00"),
        ("Route-06", "INBOUND", 1, drivers[1], "07:30:00", "08:35:00"),
        ("Route-06", "OUTBOUND", 1, drivers[1], "17:10:00", "18:15:00"),
        ("Short-01", "OUTBOUND", 5, drivers[0], "09:00:00", "09:12:00"),
        ("Short-01", "INBOUND",  5, drivers[0], "09:20:00", "09:32:00"),
        ("Short-02", "OUTBOUND", 6, drivers[0], "09:30:00", "09:40:00"),
        ("Short-02", "INBOUND",  6, drivers[0], "09:50:00", "10:00:00"),
        ("Short-03", "OUTBOUND", 6, drivers[0], "10:30:00", "10:38:00"),
        ("Short-03", "INBOUND",  6, drivers[0], "10:50:00", "10:58:00"),
        ("Faculty-01", "OUTBOUND", 7, drivers[5], "11:00:00", "11:12:00"),
        ("Faculty-01", "INBOUND",  7, drivers[5], "11:20:00", "11:32:00"),
    ]
    ids = []
    for code, d, s_idx, drv, dep, arr in rows:
        ids.append(run(cur, """
            INSERT INTO schedule
                (route_id, shuttle_id, driver_uiu_id, term_id,
                 direction, departure_time, arrival_time, operating_days)
            VALUES (%s, %s, %s, %s, %s, %s, %s, 'Mon-Fri')
        """, (R[code], sh[s_idx], drv, term_ids[0], d, dep, arr)))
    return ids


# ============================================================
# REGISTRATIONS + FACULTY AUTH
# ============================================================
def insert_registrations(cur, R, S, term_ids):
    print("🎟️  Student registrations...")
    regs = [
        ("011221001", "Route-01",  "Zigatola Bus Stop",      3000, "Paid"),
        ("011221002", "Route-01",  "Dhanmondi Keari Plaza",  3000, "Paid"),
        ("011221003", "Route-01",  "Shankar Bus Stop",       3000, "Paid"),
        ("011221004", "Route-03",  "Mirpur 10",              3500, "Paid"),
        ("011221005", "Route-03",  "Mirpur 1",               3500, "Paid"),
        ("011222006", "Route-04A", "Mugdapara",              3200, "Paid"),
        ("011222007", "Route-04A", "Aftab Nagar",            3200, "Paid"),
        ("011223008", "Route-05",  "Panthapath",             2800, "Paid"),
        ("011223009", "Route-05",  "City College",           2800, "Paid"),
        ("011223010", "Route-05",  "Azimpur",                2800, "Paid"),
        ("011223011", "Route-06",  "Airport",                2500, "Paid"),
        ("011223012", "Route-06",  "Khilkhet",               2500, "Paid"),
        ("011224013", "Route-04B", "Jatrabari Mor",          3200, "Paid"),
        ("011224014", "Route-04B", "Bashabo",                3200, "Paid"),
        ("011224015", "Route-01",  "Mohammadpur BRTC",       3000, "Paid"),
        ("011224016", "Route-03",  "Mirpur 12",              3500, "Paid"),
        ("011224017", "Route-05",  "West Kalabagan",         2800, "Pending"),
        ("011225018", "Route-06",  "Abdullahpur",            2500, "Paid"),
        ("011225019", "Route-01",  "Gulshan 2",              3000, "Paid"),
        ("011225020", "Route-03",  "Kuril Flyover",          3500, "Paid"),
    ]
    for uiu, code, stop, fee, pay in regs:
        pay_date = "2025-01-06" if pay == "Paid" else None
        run(cur, """
            INSERT INTO student_registration
                (student_uiu_id, route_id, term_id, boarding_stop_id,
                 fee_charged, payment_date, payment_status, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, 'Active')
        """, (uiu, R[code], term_ids[0], S[stop], fee, pay_date, pay))

    print("🧑‍🏫 Faculty authorizations...")
    for uiu in ["01611000001", "01611000002", "01611000003"]:
        run(cur, """
            INSERT INTO faculty_authorization
                (person_uiu_id, route_id, authorized_from, is_active)
            VALUES (%s, %s, '2025-01-05', TRUE)
        """, (uiu, R["Faculty-01"]))


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
        print("🧹 Clearing existing data...")
        cur.execute("SET FOREIGN_KEY_CHECKS = 0")
        for t in ["trip_passenger", "complaint", "maintenance", "trip",
                  "student_registration", "faculty_authorization", "schedule",
                  "route_stop", "route_fee", "route", "shuttle", "person",
                  "term_calendar", "term", "stop"]:
            cur.execute(f"DELETE FROM {t}")
        cur.execute("SET FOREIGN_KEY_CHECKS = 1")

        term_ids = insert_terms(cur)
        insert_calendar(cur, term_ids)
        S = insert_stops(cur)
        R = insert_routes(cur, S)
        insert_route_stops(cur, R, S)
        insert_route_fees(cur, R)
        sh = insert_shuttles(cur)
        insert_persons(cur)
        drivers = ["01811000001", "01811000002", "01811000003",
                   "01811000004", "01811000005", "01811000006"]
        insert_schedules(cur, R, term_ids, sh, drivers)
        insert_registrations(cur, R, S, term_ids)

        conn.commit()
        print("\n✅ Reference data inserted successfully!")

        for t in ["term", "term_calendar", "stop", "route", "route_fee",
                  "route_stop", "shuttle", "person", "schedule",
                  "student_registration", "faculty_authorization"]:
            cur.execute(f"SELECT COUNT(*) FROM {t}")
            print(f"   {t:25s} = {cur.fetchone()[0]}")
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