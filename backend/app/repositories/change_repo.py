"""Repository for flight change requests (Milestone M7)."""

import sqlite3
from typing import Any, Optional
from datetime import datetime, timedelta

from backend.app.errors import ConflictException, NotFoundException, RuleRefusalException, RuleViolationException
from backend.app.services.rules import validate_r2_pickup


def _add_minutes_iso(iso_str: str, minutes: int) -> str:
    """Add minutes to an ISO string formatted as YYYY-MM-DDTHH:MM."""
    dt = datetime.fromisoformat(iso_str)
    res = dt + timedelta(minutes=minutes)
    return res.strftime("%Y-%m-%dT%H:%M")


def create_change_request(
    conn: sqlite3.Connection,
    booking_number: str,
    new_flight_id: str,
    new_pickup_local: Optional[str] = None,
) -> dict[str, Any]:
    """Create a new flight change request for an existing confirmed booking.
    
    Validates same-airport flight and Rule R2 at submission.
    """
    cur = conn.cursor()

    # 1. Fetch current booking details
    cur.execute(
        """
        SELECT 
            b.booking_number, b.supplier_id, b.vehicle_id, b.flight_id AS old_flight_id,
            b.pickup_local AS old_pickup_local, b.request_id,
            f_old.to_airport AS airport_code
        FROM bookings b
        JOIN flights f_old ON b.flight_id = f_old.flight_id
        WHERE b.booking_number = ? AND b.is_active = 1
        """,
        (booking_number,),
    )
    b_row = cur.fetchone()
    if not b_row:
        raise NotFoundException(f"Booking {booking_number} not found.")

    airport_code = b_row["airport_code"]
    supplier_id = b_row["supplier_id"]
    old_flight_id = b_row["old_flight_id"]
    old_pickup_local = b_row["old_pickup_local"]

    # 2. Check if a WAITING change request already exists
    cur.execute(
        """
        SELECT change_id FROM change_requests
        WHERE booking_number = ? AND status = 'WAITING' AND is_active = 1
        """,
        (booking_number,),
    )
    if cur.fetchone():
        raise ConflictException(f"Booking {booking_number} already has a pending change request awaiting supplier review.")

    # 3. Fetch new flight
    cur.execute(
        """
        SELECT flight_id, to_airport, arrival_local
        FROM flights
        WHERE flight_id = ? AND is_active = 1
        """,
        (new_flight_id,),
    )
    f_new = cur.fetchone()
    if not f_new:
        raise NotFoundException(f"New flight {new_flight_id} not found.")

    if f_new["to_airport"] != airport_code:
        raise RuleRefusalException(
            rule="R9",
            field="new_flight_id",
            message=f"New flight must arrive at the same airport ({airport_code}), but {new_flight_id} arrives at {f_new['to_airport']}.",
        )

    # 4. Default or validate new pickup time (Rule R2)
    new_arrival = f_new["arrival_local"]
    if not new_pickup_local:
        # Default is landing + 60m
        new_pickup_local = _add_minutes_iso(new_arrival, 60)
    else:
        # Validate Rule R2
        validate_r2_pickup(new_pickup_local, new_arrival)

    # 5. Insert change request
    cur.execute(
        """
        INSERT INTO change_requests (
            booking_number, supplier_id, old_flight_id, old_pickup_local,
            new_flight_id, new_pickup_local, status, is_active
        ) VALUES (?, ?, ?, ?, ?, ?, 'WAITING', 1)
        """,
        (
            booking_number,
            supplier_id,
            old_flight_id,
            old_pickup_local,
            new_flight_id,
            new_pickup_local,
        ),
    )
    change_id = cur.lastrowid
    conn.commit()

    return get_change_request_by_id(conn, change_id)  # type: ignore


def get_change_request_by_id(conn: sqlite3.Connection, change_id: int) -> Optional[dict[str, Any]]:
    """Fetch change request by ID."""
    cur = conn.cursor()
    cur.execute(
        """
        SELECT 
            c.change_id, c.booking_number, c.supplier_id, c.old_flight_id, c.old_pickup_local,
            c.new_flight_id, c.new_pickup_local, c.status, c.reason, c.created_at,
            s.name AS supplier_name,
            f_new.airline AS new_airline, f_new.arrival_local AS new_arrival_local,
            b.vehicle_id, b.price_inr
        FROM change_requests c
        JOIN suppliers s ON c.supplier_id = s.supplier_id
        JOIN bookings b ON c.booking_number = b.booking_number
        JOIN flights f_new ON c.new_flight_id = f_new.flight_id
        WHERE c.change_id = ? AND c.is_active = 1
        """,
        (change_id,),
    )
    row = cur.fetchone()
    if not row:
        return None
    return dict(row)


def get_changes_for_booking(conn: sqlite3.Connection, booking_number: str) -> list[dict[str, Any]]:
    """List all change requests for a given booking."""
    cur = conn.cursor()
    cur.execute(
        """
        SELECT 
            c.change_id, c.booking_number, c.supplier_id, c.old_flight_id, c.old_pickup_local,
            c.new_flight_id, c.new_pickup_local, c.status, c.reason, c.created_at,
            f_new.airline AS new_airline, f_new.arrival_local AS new_arrival_local
        FROM change_requests c
        JOIN flights f_new ON c.new_flight_id = f_new.flight_id
        WHERE c.booking_number = ? AND c.is_active = 1
        ORDER BY c.change_id DESC
        """,
        (booking_number,),
    )
    return [dict(r) for r in cur.fetchall()]


def get_changes_for_supplier(conn: sqlite3.Connection, supplier_id: str) -> list[dict[str, Any]]:
    """List change requests assigned to a supplier."""
    cur = conn.cursor()
    cur.execute(
        """
        SELECT 
            c.change_id, c.booking_number, c.supplier_id, c.old_flight_id, c.old_pickup_local,
            c.new_flight_id, c.new_pickup_local, c.status, c.reason, c.created_at,
            b.vehicle_id, b.request_id,
            f_new.arrival_local AS new_arrival_local,
            r.traveler_name, r.city, r.area,
            h.name AS hotel_name
        FROM change_requests c
        JOIN bookings b ON c.booking_number = b.booking_number
        JOIN ride_requests r ON b.request_id = r.request_id
        JOIN hotels h ON r.hotel_id = h.hotel_id
        JOIN flights f_new ON c.new_flight_id = f_new.flight_id
        WHERE c.supplier_id = ? AND c.is_active = 1
        ORDER BY c.change_id DESC
        """,
        (supplier_id,),
    )
    return [dict(r) for r in cur.fetchall()]


def decide_change_request(
    conn: sqlite3.Connection,
    change_id: int,
    decision: str,  # 'ACCEPTED' or 'REJECTED'
    reject_reason: Optional[str] = None,
) -> dict[str, Any]:
    """Supplier accepts or rejects a change request.
    
    If ACCEPTED, re-checks Rule R2 and vehicle busy conflict:
      - If conflict occurs, auto-rejects with explanation and leaves booking untouched.
      - If free, updates booking and request flight and pickup times.
    If REJECTED, marks rejected and leaves booking untouched.
    """
    cur = conn.cursor()

    cur.execute(
        """
        SELECT 
            c.change_id, c.booking_number, c.supplier_id, c.new_flight_id, c.new_pickup_local,
            c.status,
            b.request_id, b.vehicle_id,
            r.airport_code, r.city, r.area,
            ro.drive_minutes,
            f.arrival_local AS new_arrival_local
        FROM change_requests c
        JOIN bookings b ON c.booking_number = b.booking_number
        JOIN ride_requests r ON b.request_id = r.request_id
        JOIN routes ro ON ro.airport = r.airport_code AND ro.city = r.city AND ro.area = r.area
        JOIN flights f ON c.new_flight_id = f.flight_id
        WHERE c.change_id = ? AND c.is_active = 1
        """,
        (change_id,),
    )
    row = cur.fetchone()
    if not row:
        raise NotFoundException(f"Change request #{change_id} not found.")

    if row["status"] != "WAITING":
        raise ConflictException(f"Change request #{change_id} is already {row['status']}.")

    booking_number = row["booking_number"]
    request_id = row["request_id"]
    vehicle_id = row["vehicle_id"]
    new_flight_id = row["new_flight_id"]
    new_pickup_local = row["new_pickup_local"]
    new_arrival = row["new_arrival_local"]
    drive_minutes = row["drive_minutes"]

    if decision == "REJECTED":
        reason = reject_reason or "Change request rejected by supplier."
        cur.execute(
            """
            UPDATE change_requests
            SET status = 'REJECTED', reason = ?, updated_at = CURRENT_TIMESTAMP
            WHERE change_id = ?
            """,
            (reason, change_id),
        )
        conn.commit()
        return get_change_request_by_id(conn, change_id)  # type: ignore

    # Acceptance flow:
    # 1. Re-check R2
    try:
        validate_r2_pickup(new_pickup_local, new_arrival)
    except RuleViolationException as e:
        auto_reason = f"Auto-rejected: {e.message}"
        cur.execute(
            """
            UPDATE change_requests
            SET status = 'REJECTED', reason = ?, updated_at = CURRENT_TIMESTAMP
            WHERE change_id = ?
            """,
            (auto_reason, change_id),
        )
        conn.commit()
        return get_change_request_by_id(conn, change_id)  # type: ignore

    # 2. Re-check vehicle availability
    new_busy_start = new_pickup_local
    new_busy_end = _add_minutes_iso(new_pickup_local, drive_minutes)

    cur.execute(
        """
        SELECT ride_id, start_local, end_local FROM booked_rides
        WHERE vehicle_id = ? AND is_active = 1
          AND start_local < ? AND ? < end_local
        UNION ALL
        SELECT booking_number, busy_start, busy_end FROM bookings
        WHERE vehicle_id = ? AND booking_number <> ? AND is_active = 1
          AND busy_start < ? AND ? < busy_end
        """,
        (vehicle_id, new_busy_end, new_busy_start, vehicle_id, booking_number, new_busy_end, new_busy_start),
    )
    conflict = cur.fetchone()
    if conflict:
        auto_reason = f"Auto-rejected: vehicle {vehicle_id} is busy between {conflict['start_local']} and {conflict['end_local']}."
        cur.execute(
            """
            UPDATE change_requests
            SET status = 'REJECTED', reason = ?, updated_at = CURRENT_TIMESTAMP
            WHERE change_id = ?
            """,
            (auto_reason, change_id),
        )
        conn.commit()
        return get_change_request_by_id(conn, change_id)  # type: ignore

    # 3. Passed all checks: accept and update booking + request
    cur.execute(
        """
        UPDATE change_requests
        SET status = 'ACCEPTED', reason = 'Accepted by supplier', updated_at = CURRENT_TIMESTAMP
        WHERE change_id = ?
        """,
        (change_id,),
    )

    cur.execute(
        """
        UPDATE bookings
        SET flight_id = ?, pickup_local = ?, busy_start = ?, busy_end = ?, updated_at = CURRENT_TIMESTAMP
        WHERE booking_number = ?
        """,
        (new_flight_id, new_pickup_local, new_busy_start, new_busy_end, booking_number),
    )

    cur.execute(
        """
        UPDATE ride_requests
        SET flight_id = ?, pickup_local = ?, updated_at = CURRENT_TIMESTAMP
        WHERE request_id = ?
        """,
        (new_flight_id, new_pickup_local, request_id),
    )

    conn.commit()
    return get_change_request_by_id(conn, change_id)  # type: ignore
