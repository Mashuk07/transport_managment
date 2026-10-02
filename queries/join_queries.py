"""
join_queries.py - Multi-table JOIN queries
"""
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from db import get_connection
from queries.basic_queries import run_query


def main():
    run_query("""
        SELECT rs.stop_order, s.stop_name, rs.eta_offset_min
        FROM route_stop rs
        JOIN stop s ON rs.stop_id = s.stop_id
        JOIN route r ON rs.route_id = r.route_id
        WHERE r.route_code = 'Route-01' AND rs.direction = 'INBOUND'
        ORDER BY rs.stop_order
    """, "J1: Route-01 stops in order (INBOUND)")

    run_query("""
        SELECT r.route_code, s.direction, s.departure_time, s.arrival_time,
               sh.registration_no AS bus, sh.capacity,
               p.full_name AS driver, t.term_name
        FROM schedule s
        JOIN route r ON s.route_id = r.route_id
        JOIN shuttle sh ON s.shuttle_id = sh.shuttle_id
        LEFT JOIN person p ON s.driver_uiu_id = p.uiu_id
        JOIN term t ON s.term_id = t.term_id
        WHERE r.route_code = 'Route-01'
        ORDER BY s.departure_time
    """, "J2: Route-01 schedule with bus, driver, term")

    run_query("""
        SELECT p.full_name, p.uiu_id, r.route_code, t.term_name,
               sr.fee_charged, sr.payment_status, sr.status
        FROM student_registration sr
        JOIN person p ON sr.student_uiu_id = p.uiu_id
        JOIN route r ON sr.route_id = r.route_id
        JOIN term t ON sr.term_id = t.term_id
        ORDER BY sr.registration_date DESC
        LIMIT 20
    """, "J3: All registrations (student + route + term)")

    run_query("""
        SELECT s.stop_name, s.area, COUNT(DISTINCT rs.route_id) AS route_count
        FROM stop s
        JOIN route_stop rs ON s.stop_id = rs.stop_id
        GROUP BY s.stop_id, s.stop_name, s.area
        HAVING route_count > 3
        ORDER BY route_count DESC
    """, "J4: Stops shared by more than 3 routes")

    run_query("""
        SELECT sh.registration_no, sh.shuttle_type,
               COUNT(m.maintenance_id) AS services,
               SUM(m.cost) AS total_cost
        FROM shuttle sh
        LEFT JOIN maintenance m ON sh.shuttle_id = m.shuttle_id
        GROUP BY sh.shuttle_id, sh.registration_no, sh.shuttle_type
        ORDER BY total_cost DESC
    """, "J5: Maintenance cost per shuttle")


if __name__ == "__main__":
    main()