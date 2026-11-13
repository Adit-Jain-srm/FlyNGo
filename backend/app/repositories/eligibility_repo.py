"""Eligibility and supplier dashboard queries (Appendices B.1, B.2, B.3 from docs/DESIGN.md)."""

import sqlite3
from typing import Any


def get_eligible_cars_for_request(
    conn: sqlite3.Connection,
    airport: str,
    city: str,
    area: str,
    pax: int,
    large: int,
    small: int,
    car_type: str | None,
    start_local: str,
    end_local: str,
) -> list[sqlite3.Row]:
    """B.1 Eligible cars for one request (R4, R5, R6)."""
    query = """
        SELECT s.supplier_id, v.vehicle_id
        FROM suppliers s
        JOIN supplier_airports sa ON sa.supplier_id = s.supplier_id AND sa.airport_code = :airport AND sa.is_active = 1
        JOIN supplier_areas sr ON sr.supplier_id = s.supplier_id AND sr.city = :city AND sr.area = :area AND sr.is_active = 1
        JOIN vehicles v ON v.supplier_id = s.supplier_id AND v.is_active = 1
          AND v.seats >= :pax AND v.large_bags >= :large AND v.small_bags >= :small
          AND (:car_type IS NULL OR v.type = :car_type)
        WHERE s.is_active = 1
          AND CASE WHEN s.service_from <= s.service_until
                   THEN substr(:start, 12, 5) BETWEEN s.service_from AND s.service_until
                   ELSE substr(:start, 12, 5) >= s.service_from OR substr(:start, 12, 5) <= s.service_until END
          AND NOT EXISTS (SELECT 1 FROM bookings b WHERE b.vehicle_id = v.vehicle_id AND b.is_active = 1
                          AND b.busy_start < :end AND :start < b.busy_end)
          AND NOT EXISTS (SELECT 1 FROM booked_rides x WHERE x.vehicle_id = v.vehicle_id AND x.is_active = 1
                          AND x.start_local < :end AND :start < x.end_local)
        ORDER BY s.supplier_id, v.vehicle_id;
    """
    params = {
        "airport": airport,
        "city": city,
        "area": area,
        "pax": pax,
        "large": large,
        "small": small,
        "car_type": car_type,
        "start": start_local,
        "end": end_local,
    }
    return conn.execute(query, params).fetchall()


def get_open_requests_for_supplier(
    conn: sqlite3.Connection,
    supplier_id: str,
) -> list[sqlite3.Row]:
    """B.2 Supplier dashboard: the open requests this supplier can serve."""
    query = """
        SELECT r.request_id, r.source, r.traveler_name, r.flight_id, r.hotel_id,
               r.airport_code, r.city, r.area, r.adults, r.passengers,
               r.large_bags, r.small_bags, r.pickup_local, r.car_type,
               r.price_inr, r.status, r.created_at,
               f.airline, f.flight_number, f.arrival_local,
               h.name AS hotel_name,
               rt.drive_minutes, rt.distance_km, rt.price_min_inr, rt.price_max_inr
        FROM ride_requests r
        JOIN flights f ON f.flight_id = r.flight_id AND f.is_active = 1
        JOIN hotels h ON h.hotel_id = r.hotel_id AND h.is_active = 1
        JOIN routes rt ON rt.airport = r.airport_code AND rt.city = r.city AND rt.area = r.area AND rt.is_active = 1
        JOIN suppliers s ON s.supplier_id = :supplier_id AND s.is_active = 1
        JOIN supplier_airports sa ON sa.supplier_id = s.supplier_id AND sa.airport_code = r.airport_code AND sa.is_active = 1
        JOIN supplier_areas sr ON sr.supplier_id = s.supplier_id AND sr.city = r.city AND sr.area = r.area AND sr.is_active = 1
        WHERE r.status = 'OPEN' AND r.is_active = 1
          AND CASE WHEN s.service_from <= s.service_until
                   THEN substr(r.pickup_local, 12, 5) BETWEEN s.service_from AND s.service_until
                   ELSE substr(r.pickup_local, 12, 5) >= s.service_from OR substr(r.pickup_local, 12, 5) <= s.service_until END
          AND EXISTS (
            SELECT 1 FROM vehicles v
            WHERE v.supplier_id = s.supplier_id AND v.is_active = 1
              AND v.seats >= r.passengers AND v.large_bags >= r.large_bags AND v.small_bags >= r.small_bags
              AND (r.car_type IS NULL OR v.type = r.car_type)
              AND NOT EXISTS (SELECT 1 FROM bookings b WHERE b.vehicle_id = v.vehicle_id AND b.is_active = 1
                    AND b.busy_start < strftime('%Y-%m-%dT%H:%M', r.pickup_local, '+' || (2 * rt.drive_minutes) || ' minutes')
                    AND r.pickup_local < b.busy_end)
              AND NOT EXISTS (SELECT 1 FROM booked_rides x WHERE x.vehicle_id = v.vehicle_id AND x.is_active = 1
                    AND x.start_local < strftime('%Y-%m-%dT%H:%M', r.pickup_local, '+' || (2 * rt.drive_minutes) || ' minutes')
                    AND r.pickup_local < x.end_local))
        ORDER BY r.pickup_local;
    """
    return conn.execute(query, {"supplier_id": supplier_id}).fetchall()


def get_no_supplier_funnel_counts(
    conn: sqlite3.Connection,
    airport: str,
    city: str,
    area: str,
    pax: int,
    large: int,
    small: int,
    car_type: str | None,
    start_local: str,
    end_local: str,
) -> dict[str, int]:
    """B.3 "No supplier can serve": count of suppliers passing each step."""
    query = """
        SELECT
          COALESCE(SUM(at_airport), 0)                                       AS at_airport,
          COALESCE(SUM(at_airport * in_area), 0)                             AS drives_to_area,
          COALESCE(SUM(at_airport * in_area * is_open), 0)                   AS open_at_pickup,
          COALESCE(SUM(at_airport * in_area * is_open * has_fit), 0)         AS has_fitting_car,
          COALESCE(SUM(at_airport * in_area * is_open * has_free_fit), 0)    AS has_free_fitting_car
        FROM (
          SELECT
            EXISTS (SELECT 1 FROM supplier_airports sa WHERE sa.supplier_id = s.supplier_id
                    AND sa.airport_code = :airport AND sa.is_active = 1) AS at_airport,
            EXISTS (SELECT 1 FROM supplier_areas sr WHERE sr.supplier_id = s.supplier_id
                    AND sr.city = :city AND sr.area = :area AND sr.is_active = 1) AS in_area,
            CASE WHEN s.service_from <= s.service_until
                 THEN substr(:start, 12, 5) BETWEEN s.service_from AND s.service_until
                 ELSE substr(:start, 12, 5) >= s.service_from OR substr(:start, 12, 5) <= s.service_until END AS is_open,
            EXISTS (SELECT 1 FROM vehicles v WHERE v.supplier_id = s.supplier_id AND v.is_active = 1
                    AND v.seats >= :pax AND v.large_bags >= :large AND v.small_bags >= :small
                    AND (:car_type IS NULL OR v.type = :car_type)) AS has_fit,
            EXISTS (SELECT 1 FROM vehicles v WHERE v.supplier_id = s.supplier_id AND v.is_active = 1
                    AND v.seats >= :pax AND v.large_bags >= :large AND v.small_bags >= :small
                    AND (:car_type IS NULL OR v.type = :car_type)
                    AND NOT EXISTS (SELECT 1 FROM bookings b WHERE b.vehicle_id = v.vehicle_id AND b.is_active = 1
                                    AND b.busy_start < :end AND :start < b.busy_end)
                    AND NOT EXISTS (SELECT 1 FROM booked_rides x WHERE x.vehicle_id = v.vehicle_id AND x.is_active = 1
                                    AND x.start_local < :end AND :start < x.end_local)) AS has_free_fit
          FROM suppliers s
          WHERE s.is_active = 1
        );
    """
    params = {
        "airport": airport,
        "city": city,
        "area": area,
        "pax": pax,
        "large": large,
        "small": small,
        "car_type": car_type,
        "start": start_local,
        "end": end_local,
    }
    row = conn.execute(query, params).fetchone()
    if not row:
        return {
            "at_airport": 0,
            "drives_to_area": 0,
            "open_at_pickup": 0,
            "has_fitting_car": 0,
            "has_free_fitting_car": 0,
        }
    return dict(row)


def get_supplier_fleet_with_badges(
    conn: sqlite3.Connection,
    supplier_id: str,
    passengers: int,
    large_bags: int,
    small_bags: int,
    car_type: str | None,
    start_local: str,
    end_local: str,
) -> list[dict[str, Any]]:
    """Evaluate every vehicle belonging to a supplier and assign advisory badges."""
    vehicles = conn.execute(
        """
        SELECT vehicle_id, supplier_id, type, seats, large_bags, small_bags
        FROM vehicles
        WHERE supplier_id = ? AND is_active = 1
        ORDER BY type, seats;
        """,
        (supplier_id,),
    ).fetchall()

    results: list[dict[str, Any]] = []

    for v in vehicles:
        vid = v["vehicle_id"]
        v_dict = dict(v)

        # 1. Car type mismatch
        if car_type and v["type"] != car_type:
            v_dict["badge"] = "WRONG_TYPE"
            v_dict["reason"] = f"Wrong type: vehicle is {v['type']}, request requires {car_type}"
            v_dict["busy_until"] = None
            v_dict["is_selectable"] = True
            results.append(v_dict)
            continue

        # 2. Capacity: Seats
        if v["seats"] < passengers:
            v_dict["badge"] = "TOO_SMALL"
            v_dict["reason"] = f"Too small: {v['seats']} seats < {passengers} passengers"
            v_dict["busy_until"] = None
            v_dict["is_selectable"] = True
            results.append(v_dict)
            continue

        # 3. Capacity: Luggage
        if v["large_bags"] < large_bags:
            v_dict["badge"] = "TOO_SMALL"
            v_dict["reason"] = f"Too small: {v['large_bags']} large bags < {large_bags} required"
            v_dict["busy_until"] = None
            v_dict["is_selectable"] = True
            results.append(v_dict)
            continue

        if v["small_bags"] < small_bags:
            v_dict["badge"] = "TOO_SMALL"
            v_dict["reason"] = f"Too small: {v['small_bags']} small bags < {small_bags} required"
            v_dict["busy_until"] = None
            v_dict["is_selectable"] = True
            results.append(v_dict)
            continue

        # 4. Schedule Availability: Check bookings and booked_rides
        conflicts = conn.execute(
            """
            SELECT busy_end AS conflict_end
            FROM bookings
            WHERE vehicle_id = ? AND is_active = 1
              AND busy_start < ? AND ? < busy_end
            UNION ALL
            SELECT end_local AS conflict_end
            FROM booked_rides
            WHERE vehicle_id = ? AND is_active = 1
              AND start_local < ? AND ? < end_local
            ORDER BY conflict_end DESC;
            """,
            (vid, end_local, start_local, vid, end_local, start_local),
        ).fetchall()

        if conflicts:
            max_end = conflicts[0]["conflict_end"]
            v_dict["badge"] = "BUSY"
            v_dict["reason"] = f"Busy until {max_end[11:16]}"
            v_dict["busy_until"] = max_end
            v_dict["is_selectable"] = True
        else:
            v_dict["badge"] = "FITS_FREE"
            v_dict["reason"] = "Fits and free"
            v_dict["busy_until"] = None
            v_dict["is_selectable"] = True

        results.append(v_dict)

    return results
