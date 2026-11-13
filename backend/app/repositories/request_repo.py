"""Request repository for ride request persistence and querying."""

import re
import sqlite3
from typing import Any


def get_next_request_id(conn: sqlite3.Connection) -> str:
    """Generate the next sequential request ID formatted as REQ-XXXX.

    Example: If max request is REQ-0003, returns REQ-0004.
    """
    rows = conn.execute(
        "SELECT request_id FROM ride_requests WHERE request_id LIKE 'REQ-%'"
    ).fetchall()

    max_num = 0
    pattern = re.compile(r"^REQ-(\d+)$")
    for row in rows:
        match = pattern.match(row["request_id"])
        if match:
            num = int(match.group(1))
            if num > max_num:
                max_num = num

    return f"REQ-{max_num + 1:04d}"


def create_ride_request(
    conn: sqlite3.Connection,
    request_id: str,
    source: str,
    traveler_name: str | None,
    flight_id: str,
    hotel_id: str,
    airport_code: str,
    city: str,
    area: str,
    adults: int,
    passengers: int,
    large_bags: int,
    small_bags: int,
    pickup_local: str,
    car_type: str | None,
    price_inr: int,
    child_ages: list[int],
) -> str:
    """Insert a new ride request and its associated children in a transaction."""
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO ride_requests (
            request_id, source, traveler_name, flight_id, hotel_id,
            airport_code, city, area, adults, passengers,
            large_bags, small_bags, pickup_local, car_type,
            price_inr, status, is_active, updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'OPEN', 1, CURRENT_TIMESTAMP);
        """,
        (
            request_id,
            source,
            traveler_name,
            flight_id,
            hotel_id,
            airport_code,
            city,
            area,
            adults,
            passengers,
            large_bags,
            small_bags,
            pickup_local,
            car_type,
            price_inr,
        ),
    )

    for idx, age in enumerate(child_ages, start=1):
        cur.execute(
            """
            INSERT INTO request_children (request_id, child_no, age, is_active, updated_at)
            VALUES (?, ?, ?, 1, CURRENT_TIMESTAMP);
            """,
            (request_id, idx, age),
        )

    return request_id


def get_request_by_id(conn: sqlite3.Connection, request_id: str) -> dict[str, Any] | None:
    """Retrieve full details of a ride request including joined flight, hotel, and children."""
    query = """
        SELECT r.*,
               f.airline, f.flight_number, f.arrival_local,
               h.name AS hotel_name,
               rt.price_min_inr, rt.price_max_inr
        FROM ride_requests r
        JOIN flights f ON f.flight_id = r.flight_id AND f.is_active = 1
        JOIN hotels h ON h.hotel_id = r.hotel_id AND h.is_active = 1
        LEFT JOIN routes rt ON rt.airport = r.airport_code AND rt.city = r.city AND rt.area = r.area AND rt.is_active = 1
        WHERE r.request_id = ? AND r.is_active = 1;
    """
    row = conn.execute(query, (request_id,)).fetchone()
    if not row:
        return None

    req_dict = dict(row)

    # Fetch children
    children_rows = conn.execute(
        """
        SELECT child_no, age FROM request_children
        WHERE request_id = ? AND is_active = 1
        ORDER BY child_no;
        """,
        (request_id,),
    ).fetchall()

    req_dict["children"] = [dict(c) for c in children_rows]
    return req_dict


def list_requests(
    conn: sqlite3.Connection,
    status_filter: str | None = None,
) -> list[dict[str, Any]]:
    """List ride requests with joined flight and hotel details."""
    if status_filter:
        query = """
            SELECT r.*,
                   f.airline, f.flight_number, f.arrival_local,
                   h.name AS hotel_name,
                   rt.price_min_inr, rt.price_max_inr
            FROM ride_requests r
            JOIN flights f ON f.flight_id = r.flight_id AND f.is_active = 1
            JOIN hotels h ON h.hotel_id = r.hotel_id AND h.is_active = 1
            LEFT JOIN routes rt ON rt.airport = r.airport_code AND rt.city = r.city AND rt.area = r.area AND rt.is_active = 1
            WHERE r.status = ? AND r.is_active = 1
            ORDER BY r.created_at DESC;
        """
        rows = conn.execute(query, (status_filter,)).fetchall()
    else:
        query = """
            SELECT r.*,
                   f.airline, f.flight_number, f.arrival_local,
                   h.name AS hotel_name,
                   rt.price_min_inr, rt.price_max_inr
            FROM ride_requests r
            JOIN flights f ON f.flight_id = r.flight_id AND f.is_active = 1
            JOIN hotels h ON h.hotel_id = r.hotel_id AND h.is_active = 1
            LEFT JOIN routes rt ON rt.airport = r.airport_code AND rt.city = r.city AND rt.area = r.area AND rt.is_active = 1
            WHERE r.is_active = 1
            ORDER BY r.created_at DESC;
        """
        rows = conn.execute(query).fetchall()

    results = []
    for row in rows:
        req_dict = dict(row)
        children_rows = conn.execute(
            "SELECT child_no, age FROM request_children WHERE request_id = ? AND is_active = 1 ORDER BY child_no;",
            (row["request_id"],),
        ).fetchall()
        req_dict["children"] = [dict(c) for c in children_rows]
        results.append(req_dict)

    return results
