"""
aggregate_queries.py - GROUP BY, SUM, COUNT, AVG, HAVING
"""
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from queries.basic_queries import run_query


def main():
    run_query("""
        SELECT r.route_code, r.route_name,
               COUNT(sr.registration_id) AS students,
               SUM(sr.fee_charged) AS total_revenue
        FROM route r
        LEFT JOIN student_registration sr
          ON r.route_id = sr.route_id AND sr.payment_status = 'Paid'
        WHERE r.service_type = 'RouteService'
        GROUP BY r.route_id, r.route_code, r.route_name
        ORDER BY total_revenue DESC
    """, "A1: Revenue per paid route")

    run_query("""
        SELECT t.term_type,
               COUNT(sr.registration_id) AS students,
               SUM(sr.fee_charged) AS revenue,
               ROUND(AVG(sr.fee_charged), 2) AS avg_fee
        FROM student_registration sr
        JOIN term t ON sr.term_id = t.term_id
        WHERE sr.payment_status = 'Paid'
        GROUP BY t.term_type
    """, "A2: Trimester vs Semester revenue comparison")

    run_query("""
        SELECT r.route_code,
               COUNT(t.trip_id) AS trips,
               ROUND(AVG(t.passenger_count), 1) AS avg_passengers,
               MAX(t.passenger_count) AS max_passengers
        FROM trip t
        JOIN schedule s ON t.schedule_id = s.schedule_id
        JOIN route r ON s.route_id = r.route_id
        WHERE t.status <> 'Cancelled'
        GROUP BY r.route_id, r.route_code
        ORDER BY avg_passengers DESC
    """, "A3: Average passengers per trip by route")

    run_query("""
        SELECT s.stop_name, s.area, COUNT(*) AS boardings
        FROM trip_passenger tp
        JOIN stop s ON tp.stop_id = s.stop_id
        GROUP BY s.stop_id, s.stop_name, s.area
        ORDER BY boardings DESC
        LIMIT 5
    """, "A4: Top 5 boarding stops")

    run_query("""
        SELECT status, COUNT(*) AS trips
        FROM trip
        GROUP BY status
        ORDER BY trips DESC
    """, "A5: Trips by status")

    run_query("""
        SELECT category,
               COUNT(*) AS total,
               SUM(CASE WHEN status='Resolved' THEN 1 ELSE 0 END) AS resolved,
               ROUND(100.0 * SUM(CASE WHEN status='Resolved' THEN 1 ELSE 0 END) / COUNT(*), 1) AS pct
        FROM complaint
        GROUP BY category
        ORDER BY pct DESC
    """, "A6: Complaint resolution rate by category")


if __name__ == "__main__":
    main()