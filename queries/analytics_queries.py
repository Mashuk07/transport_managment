"""
analytics_queries.py - Advanced analytics: anti-joins, delays, window functions
"""
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from queries.basic_queries import run_query


def main():
    run_query("""
        SELECT t.trip_id, t.trip_date, r.route_code,
               t.passenger_count, sh.capacity,
               (t.passenger_count - sh.capacity) AS overflow
        FROM trip t
        JOIN schedule s ON t.schedule_id = s.schedule_id
        JOIN route r ON s.route_id = r.route_id
        JOIN shuttle sh ON t.shuttle_id = sh.shuttle_id
        WHERE t.passenger_count > sh.capacity
        ORDER BY overflow DESC
        LIMIT 10
    """, "AN1: Overcrowded trips")

    run_query("""
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
    """, "AN2: Paid but never boarded (anti-join)")

    run_query("""
        SELECT p.full_name, r.route_code, COUNT(*) AS walkon_count
        FROM trip_passenger tp
        JOIN person p ON tp.person_uiu_id = p.uiu_id
        JOIN trip t ON tp.trip_id = t.trip_id
        JOIN schedule s ON t.schedule_id = s.schedule_id
        JOIN route r ON s.route_id = r.route_id
        WHERE tp.boarding_type = 'WalkOn'
          AND r.service_type = 'RouteService'
        GROUP BY p.uiu_id, p.full_name, r.route_code
        ORDER BY walkon_count DESC
        LIMIT 10
    """, "AN3: Unregistered boarders (walk-ons)")

    run_query("""
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
    """, "AN4: Delay analysis by route")

    run_query("""
        SELECT route_code, avg_delay_min,
               RANK() OVER (ORDER BY avg_delay_min DESC) AS delay_rank
        FROM (
            SELECT r.route_code,
                   ROUND(AVG(TIME_TO_SEC(TIMEDIFF(TIME(t.actual_departure), s.departure_time)) / 60), 1) AS avg_delay_min
            FROM trip t
            JOIN schedule s ON t.schedule_id = s.schedule_id
            JOIN route r ON s.route_id = r.route_id
            WHERE t.actual_departure IS NOT NULL AND t.status <> 'Cancelled'
            GROUP BY r.route_id, r.route_code
        ) sub
    """, "AN5: Routes ranked by delay (window function)")

    run_query("""
        SELECT sh.registration_no, sh.capacity,
               ROUND(AVG(t.passenger_count / sh.capacity) * 100, 1) AS avg_utilization_pct
        FROM shuttle sh
        JOIN trip t ON sh.shuttle_id = t.shuttle_id
        WHERE t.status <> 'Cancelled'
        GROUP BY sh.shuttle_id, sh.registration_no, sh.capacity
        HAVING avg_utilization_pct < 50
        ORDER BY avg_utilization_pct
    """, "AN6: Underutilized shuttles (< 50%)")

    run_query("""
        SELECT HOUR(boarded_at) AS hour_of_day, COUNT(*) AS boardings
        FROM trip_passenger
        GROUP BY HOUR(boarded_at)
        ORDER BY boardings DESC
    """, "AN7: Peak boarding hours")


if __name__ == "__main__":
    main()