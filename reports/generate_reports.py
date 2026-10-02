"""
reports.py - Generate formatted reports and save to text files
Run: python queries/reports.py
"""
import sys
import os
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from db import get_connection


# Where to save report files
REPORTS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "reports")
os.makedirs(REPORTS_DIR, exist_ok=True)


def fetch(sql, params=None):
    conn = get_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute(sql, params or ())
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows


def fmt_table(rows, headers=None, widths=None):
    """Format rows as a plain text table."""
    if not rows:
        return "   (no data)\n"
    headers = headers or list(rows[0].keys())
    if not widths:
        widths = []
        for h in headers:
            w = max(len(str(h)), max(len(str(r[h])[:25]) for r in rows))
            widths.append(min(w, 30))

    out = []
    out.append("   " + " | ".join(f"{h:<{w}}" for h, w in zip(headers, widths)))
    out.append("   " + "-+-".join("-" * w for w in widths))
    for r in rows:
        out.append("   " + " | ".join(f"{str(r[h])[:30]:<{w}}" for h, w in zip(headers, widths)))
    return "\n".join(out) + "\n"


def save_report(name, content):
    path = os.path.join(REPORTS_DIR, f"{name}.txt")
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"   ✅ Saved: {path}")


# ============================================================
# REPORT 1: REVENUE PER ROUTE
# ============================================================
def report_revenue():
    print("\n" + "=" * 70)
    print("  REPORT 1: REVENUE PER ROUTE")
    print("=" * 70)

    rows = fetch("""
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

    total_students = sum(r['students'] for r in rows)
    total_revenue = sum(float(r['revenue']) for r in rows)

    out = []
    out.append("=" * 70)
    out.append("  REVENUE REPORT — PAID ROUTES")
    out.append(f"  Generated: {datetime.now():%Y-%m-%d %H:%M}")
    out.append("=" * 70)
    out.append("")
    out.append(fmt_table(rows))
    out.append("")
    out.append(f"   TOTAL STUDENTS: {total_students}")
    out.append(f"   TOTAL REVENUE:  {total_revenue:,.0f} BDT")
    out.append("")
    out.append("   INSIGHT: Route-01 and Route-03 generate the most revenue.")
    out.append("=" * 70)

    content = "\n".join(out)
    print(content)
    save_report("01_revenue_report", content)


# ============================================================
# REPORT 2: TRIMESTER VS SEMESTER REVENUE
# ============================================================
def report_term_comparison():
    print("\n" + "=" * 70)
    print("  REPORT 2: TRIMESTER vs SEMESTER REVENUE")
    print("=" * 70)

    rows = fetch("""
        SELECT t.term_type,
               COUNT(sr.registration_id) AS students,
               COALESCE(SUM(sr.fee_charged), 0) AS revenue,
               ROUND(AVG(sr.fee_charged), 2) AS avg_fee
        FROM student_registration sr
        JOIN term t ON sr.term_id = t.term_id
        WHERE sr.payment_status = 'Paid'
        GROUP BY t.term_type
    """)

    out = []
    out.append("=" * 70)
    out.append("  TERM TYPE COMPARISON — TRIMESTER vs SEMESTER")
    out.append(f"  Generated: {datetime.now():%Y-%m-%d %H:%M}")
    out.append("=" * 70)
    out.append("")
    out.append(fmt_table(rows))
    out.append("")
    out.append("   INSIGHT: Trimester students pay lower fees than Semester students")
    out.append("            for the same routes. This reflects the shorter duration.")
    out.append("=" * 70)

    content = "\n".join(out)
    print(content)
    save_report("02_term_comparison", content)


# ============================================================
# REPORT 3: OVERCROWDED TRIPS
# ============================================================
def report_overcrowded():
    print("\n" + "=" * 70)
    print("  REPORT 3: OVERCROWDED TRIPS")
    print("=" * 70)

    rows = fetch("""
        SELECT t.trip_id, t.trip_date, r.route_code,
               t.passenger_count, sh.capacity,
               (t.passenger_count - sh.capacity) AS overflow
        FROM trip t
        JOIN schedule s ON t.schedule_id = s.schedule_id
        JOIN route r ON s.route_id = r.route_id
        JOIN shuttle sh ON t.shuttle_id = sh.shuttle_id
        WHERE t.passenger_count > sh.capacity
        ORDER BY overflow DESC
        LIMIT 20
    """)

    out = []
    out.append("=" * 70)
    out.append("  OVERCROWDING REPORT")
    out.append(f"  Generated: {datetime.now():%Y-%m-%d %H:%M}")
    out.append("=" * 70)
    out.append("")
    out.append(fmt_table(rows))
    out.append("")
    out.append(f"   TOTAL OVERCROWDED TRIPS: {len(rows)}")
    out.append("")
    out.append("   INSIGHT: Overcrowding indicates inadequate capacity on these routes.")
    out.append("            The university should assign larger buses or add trips.")
    out.append("=" * 70)

    content = "\n".join(out)
    print(content)
    save_report("03_overcrowded_trips", content)


# ============================================================
# REPORT 4: PAID BUT NEVER BOARDED
# ============================================================
def report_never_boarded():
    print("\n" + "=" * 70)
    print("  REPORT 4: PAID BUT NEVER BOARDED")
    print("=" * 70)

    rows = fetch("""
        SELECT p.uiu_id, p.full_name, r.route_code, sr.fee_charged
        FROM student_registration sr
        JOIN person p ON sr.student_uiu_id = p.uiu_id
        JOIN route r ON sr.route_id = r.route_id
        WHERE sr.payment_status = 'Paid'
          AND sr.status = 'Active'
          AND NOT EXISTS (
              SELECT 1 FROM trip_passenger tp
              WHERE tp.person_uiu_id = sr.student_uiu_id
          )
        ORDER BY sr.fee_charged DESC
    """)

    total = sum(float(r['fee_charged']) for r in rows)

    out = []
    out.append("=" * 70)
    out.append("  WASTED REVENUE REPORT — PAID BUT NEVER BOARDED")
    out.append(f"  Generated: {datetime.now():%Y-%m-%d %H:%M}")
    out.append("=" * 70)
    out.append("")
    out.append(fmt_table(rows))
    out.append("")
    out.append(f"   TOTAL STUDENTS: {len(rows)}")
    out.append(f"   UNUSED REVENUE: {total:,.0f} BDT")
    out.append("")
    out.append("   INSIGHT: These students paid for the shuttle but never used it.")
    out.append("            Could indicate: dropped courses, alternate transport, or")
    out.append("            refund eligibility. Worth investigating.")
    out.append("=" * 70)

    content = "\n".join(out)
    print(content)
    save_report("04_never_boarded", content)


# ============================================================
# REPORT 5: DELAY ANALYSIS
# ============================================================
def report_delay():
    print("\n" + "=" * 70)
    print("  REPORT 5: DELAY ANALYSIS")
    print("=" * 70)

    rows = fetch("""
        SELECT r.route_code,
               COUNT(*) AS trips,
               ROUND(AVG(TIME_TO_SEC(TIMEDIFF(TIME(t.actual_departure), s.departure_time)) / 60), 1) AS avg_delay_min,
               MAX(TIME_TO_SEC(TIMEDIFF(TIME(t.actual_departure), s.departure_time)) / 60) AS max_delay_min
        FROM trip t
        JOIN schedule s ON t.schedule_id = s.schedule_id
        JOIN route r ON s.route_id = r.route_id
        WHERE t.actual_departure IS NOT NULL
          AND t.status <> 'Cancelled'
        GROUP BY r.route_id, r.route_code
        ORDER BY avg_delay_min DESC
    """)

    out = []
    out.append("=" * 70)
    out.append("  DELAY ANALYSIS REPORT")
    out.append(f"  Generated: {datetime.now():%Y-%m-%d %H:%M}")
    out.append("=" * 70)
    out.append("")
    out.append(fmt_table(rows))
    out.append("")
    out.append("   INSIGHT: Routes with highest average delay need investigation.")
    out.append("            Causes could be traffic, driver behavior, or route design.")
    out.append("=" * 70)

    content = "\n".join(out)
    print(content)
    save_report("05_delay_analysis", content)


# ============================================================
# REPORT 6: COMPLAINTS SUMMARY
# ============================================================
def report_complaints():
    print("\n" + "=" * 70)
    print("  REPORT 6: COMPLAINTS SUMMARY")
    print("=" * 70)

    rows = fetch("""
        SELECT category,
               COUNT(*) AS total,
               SUM(CASE WHEN status='Resolved' THEN 1 ELSE 0 END) AS resolved,
               SUM(CASE WHEN status='Open' THEN 1 ELSE 0 END) AS open_cnt,
               ROUND(100.0 * SUM(CASE WHEN status='Resolved' THEN 1 ELSE 0 END) / COUNT(*), 1) AS pct_resolved
        FROM complaint
        GROUP BY category
        ORDER BY total DESC
    """)

    out = []
    out.append("=" * 70)
    out.append("  COMPLAINTS SUMMARY REPORT")
    out.append(f"  Generated: {datetime.now():%Y-%m-%d %H:%M}")
    out.append("=" * 70)
    out.append("")
    out.append(fmt_table(rows))
    out.append("")
    out.append("   INSIGHT: High 'Open' counts indicate unresolved service issues.")
    out.append("=" * 70)

    content = "\n".join(out)
    print(content)
    save_report("06_complaints", content)


# ============================================================
# REPORT 7: MAINTENANCE COST PER SHUTTLE
# ============================================================
def report_maintenance():
    print("\n" + "=" * 70)
    print("  REPORT 7: MAINTENANCE COST PER SHUTTLE")
    print("=" * 70)

    rows = fetch("""
        SELECT sh.registration_no, sh.shuttle_type, sh.capacity,
               COUNT(m.maintenance_id) AS services,
               COALESCE(SUM(m.cost), 0) AS total_cost
        FROM shuttle sh
        LEFT JOIN maintenance m ON sh.shuttle_id = m.shuttle_id
        GROUP BY sh.shuttle_id, sh.registration_no, sh.shuttle_type, sh.capacity
        ORDER BY total_cost DESC
    """)

    total = sum(float(r['total_cost']) for r in rows)

    out = []
    out.append("=" * 70)
    out.append("  FLEET MAINTENANCE COST REPORT")
    out.append(f"  Generated: {datetime.now():%Y-%m-%d %H:%M}")
    out.append("=" * 70)
    out.append("")
    out.append(fmt_table(rows))
    out.append("")
    out.append(f"   TOTAL FLEET MAINTENANCE COST: {total:,.0f} BDT")
    out.append("=" * 70)

    content = "\n".join(out)
    print(content)
    save_report("07_maintenance", content)


# ============================================================
# REPORT 8: ROUTE POPULARITY
# ============================================================
def report_popularity():
    print("\n" + "=" * 70)
    print("  REPORT 8: ROUTE POPULARITY")
    print("=" * 70)

    rows = fetch("""
        SELECT r.route_code,
               COUNT(DISTINCT sr.registration_id) AS registrations,
               COUNT(DISTINCT t.trip_id) AS trips,
               COALESCE(SUM(t.passenger_count), 0) AS total_passengers,
               ROUND(COALESCE(AVG(t.passenger_count), 0), 1) AS avg_per_trip
        FROM route r
        LEFT JOIN student_registration sr
          ON r.route_id = sr.route_id AND sr.status = 'Active'
        LEFT JOIN schedule s ON r.route_id = s.route_id
        LEFT JOIN trip t ON s.schedule_id = t.schedule_id AND t.status <> 'Cancelled'
        WHERE r.service_type = 'RouteService'
        GROUP BY r.route_id, r.route_code
        ORDER BY total_passengers DESC
    """)

    out = []
    out.append("=" * 70)
    out.append("  ROUTE POPULARITY REPORT")
    out.append(f"  Generated: {datetime.now():%Y-%m-%d %H:%M}")
    out.append("=" * 70)
    out.append("")
    out.append(fmt_table(rows))
    out.append("")
    out.append("   INSIGHT: Highest-demand routes should receive larger buses")
    out.append("            and more frequent trips.")
    out.append("=" * 70)

    content = "\n".join(out)
    print(content)
    save_report("08_popularity", content)


# ============================================================
# REPORT 9: TOP STOPS
# ============================================================
def report_top_stops():
    print("\n" + "=" * 70)
    print("  REPORT 9: TOP BOARDING STOPS")
    print("=" * 70)

    rows = fetch("""
        SELECT s.stop_name, s.area, COUNT(*) AS boardings
        FROM trip_passenger tp
        JOIN stop s ON tp.stop_id = s.stop_id
        GROUP BY s.stop_id, s.stop_name, s.area
        ORDER BY boardings DESC
        LIMIT 15
    """)

    out = []
    out.append("=" * 70)
    out.append("  TOP BOARDING STOPS REPORT")
    out.append(f"  Generated: {datetime.now():%Y-%m-%d %H:%M}")
    out.append("=" * 70)
    out.append("")
    out.append(fmt_table(rows))
    out.append("")
    out.append("   INSIGHT: Highest-traffic stops indicate where students")
    out.append("            concentrate. Could justify more services.")
    out.append("=" * 70)

    content = "\n".join(out)
    print(content)
    save_report("09_top_stops", content)


# ============================================================
# REPORT 10: FLEET UTILIZATION
# ============================================================
def report_utilization():
    print("\n" + "=" * 70)
    print("  REPORT 10: SHUTTLE UTILIZATION")
    print("=" * 70)

    rows = fetch("""
        SELECT sh.registration_no, sh.capacity,
               COUNT(t.trip_id) AS trips,
               ROUND(AVG(t.passenger_count), 1) AS avg_passengers,
               ROUND(AVG(t.passenger_count / sh.capacity) * 100, 1) AS utilization_pct
        FROM shuttle sh
        LEFT JOIN trip t ON sh.shuttle_id = t.shuttle_id AND t.status <> 'Cancelled'
        GROUP BY sh.shuttle_id, sh.registration_no, sh.capacity
        ORDER BY utilization_pct DESC
    """)

    out = []
    out.append("=" * 70)
    out.append("  SHUTTLE UTILIZATION REPORT")
    out.append(f"  Generated: {datetime.now():%Y-%m-%d %H:%M}")
    out.append("=" * 70)
    out.append("")
    out.append(fmt_table(rows))
    out.append("")
    out.append("   INSIGHT: Low-utilization buses could be reassigned to")
    out.append("            higher-demand routes, or replaced with smaller vehicles.")
    out.append("=" * 70)

    content = "\n".join(out)
    print(content)
    save_report("10_utilization", content)


# ============================================================
# MAIN — Run all reports
# ============================================================
def main():
    print("\n" + "█" * 70)
    print("  USSMS — GENERATING ALL REPORTS")
    print("█" * 70)

    report_revenue()
    report_term_comparison()
    report_overcrowded()
    report_never_boarded()
    report_delay()
    report_complaints()
    report_maintenance()
    report_popularity()
    report_top_stops()
    report_utilization()

    print("\n" + "█" * 70)
    print(f"  ✅ ALL REPORTS GENERATED — saved to: {REPORTS_DIR}")
    print("█" * 70)


if __name__ == "__main__":
    main()