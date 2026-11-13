"""Repository for creating, querying, and managing ride bookings."""

import secrets
import sqlite3
from datetime import datetime
from typing import Any, Optional

from backend.app.errors import ConflictException, NotFoundException
from backend.app.services.rules import compute_ride_busy_interval


def generate_booking_number(conn: sqlite3.Connection) -> str:
    """Generate a unique 10-digit booking number where the first digit is 1-9.
    
    Format constraint: length 10, all digits, first digit <> '0'.
    """
    for _ in range(100):
        # 1_000_000_000 to 9_999_999_999 inclusive
        num = str(secrets.randbelow(9_000_000_000) + 1_000_000_000)
        cur = conn.cursor()
        cur.execute(
            "SELECT 1 FROM bookings WHERE booking_number = ? AND is_active = 1",
            (num,),
        )
        if cur.fetchone() is None:
            return num
    raise RuntimeError("Failed to generate unique 10-digit booking number after 100 attempts")


def create_booking_atomic(conn: sqlite3.Connection, offer_id: int) -> dict[str, Any]:
    """Atomically books an open offer and request, sets competitor offers to NOT_CHOSEN.
    
    Verifies that the vehicle is still free for the duration of the trip.
    """
    cur = conn.cursor()
    
    # 1. Fetch offer details
    cur.execute(
        """
        SELECT 
            o.offer_id, o.request_id, o.supplier_id, o.vehicle_id, o.price_inr, o.status, o.expires_at,
            r.status AS request_status, r.flight_id, r.hotel_id, r.pickup_local, r.airport_code,
            r.city, r.area, ro.drive_minutes
        FROM offers o
        JOIN ride_requests r ON o.request_id = r.request_id
        JOIN routes ro ON ro.airport = r.airport_code AND ro.city = r.city AND ro.area = r.area
        WHERE o.offer_id = ? AND o.is_active = 1 AND r.is_active = 1 AND ro.is_active = 1
        """,
        (offer_id,),
    )
    row = cur.fetchone()
    if not row:
        raise NotFoundException(f"Offer #{offer_id} not found.")

    offer_status = row["status"]
    request_status = row["request_status"]
    request_id = row["request_id"]
    supplier_id = row["supplier_id"]
    vehicle_id = row["vehicle_id"]
    price_inr = row["price_inr"]
    flight_id = row["flight_id"]
    pickup_local = row["pickup_local"]
    drive_minutes = row["drive_minutes"]

    if offer_status != "OPEN":
        raise ConflictException(f"Offer #{offer_id} is not open (status: {offer_status}).")

    expires_at = row["expires_at"]
    if expires_at and expires_at[:16] <= datetime.now().strftime("%Y-%m-%dT%H:%M"):
        raise ConflictException(
            rule="G4",
            field="expires_at",
            message=f"This offer ended at {expires_at[:16]} and cannot be booked.",
        )

    if request_status != "OPEN":
        raise ConflictException(f"Request {request_id} has already been booked or closed.")

    # 2. Check if a booking already exists for this request
    cur.execute(
        "SELECT booking_number FROM bookings WHERE request_id = ? AND is_active = 1",
        (request_id,),
    )
    if cur.fetchone():
        raise ConflictException(f"Request {request_id} is already booked.")

    # Busy from pickup until the car is back at the airport: 2 x one-way drive.
    busy_start, busy_end = compute_ride_busy_interval(pickup_local, drive_minutes)

    # 4. Re-verify vehicle availability (booked_rides and bookings)
    cur.execute(
        """
        SELECT ride_id, start_local, end_local FROM booked_rides
        WHERE vehicle_id = ? AND is_active = 1
          AND start_local < ? AND ? < end_local
        UNION ALL
        SELECT booking_number, busy_start, busy_end FROM bookings
        WHERE vehicle_id = ? AND is_active = 1
          AND busy_start < ? AND ? < busy_end
        """,
        (vehicle_id, busy_end, busy_start, vehicle_id, busy_end, busy_start),
    )
    conflict = cur.fetchone()
    if conflict:
        raise ConflictException(
            f"Vehicle {vehicle_id} is no longer available at {busy_start} (conflicts with ride until {conflict['end_local']})."
        )

    # 5. Generate 10-digit booking number
    booking_number = generate_booking_number(conn)

    # 6. Execute atomic state transitions
    # Insert booking
    cur.execute(
        """
        INSERT INTO bookings (
            booking_number, request_id, offer_id, supplier_id, vehicle_id,
            flight_id, pickup_local, busy_start, busy_end, price_inr, status, is_active
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'CONFIRMED', 1)
        """,
        (
            booking_number,
            request_id,
            offer_id,
            supplier_id,
            vehicle_id,
            flight_id,
            pickup_local,
            busy_start,
            busy_end,
            price_inr,
        ),
    )

    # Mark this offer as BOOKED
    cur.execute(
        """
        UPDATE offers
        SET status = 'BOOKED', updated_at = CURRENT_TIMESTAMP
        WHERE offer_id = ? AND is_active = 1
        """,
        (offer_id,),
    )

    # Mark other open offers for this request as NOT_CHOSEN
    cur.execute(
        """
        UPDATE offers
        SET status = 'NOT_CHOSEN', updated_at = CURRENT_TIMESTAMP
        WHERE request_id = ? AND offer_id <> ? AND status = 'OPEN' AND is_active = 1
        """,
        (request_id, offer_id),
    )

    # Mark request as BOOKED
    cur.execute(
        """
        UPDATE ride_requests
        SET status = 'BOOKED', updated_at = CURRENT_TIMESTAMP
        WHERE request_id = ? AND is_active = 1
        """,
        (request_id,),
    )

    conn.commit()

    return get_booking_by_number(conn, booking_number)  # type: ignore


def get_booking_by_number(conn: sqlite3.Connection, booking_number: str) -> Optional[dict[str, Any]]:
    """Retrieve complete booking summary by 10-digit booking number."""
    cur = conn.cursor()
    cur.execute(
        """
        SELECT 
            b.booking_number, b.request_id, b.offer_id, b.supplier_id, b.vehicle_id,
            b.flight_id, b.pickup_local, b.busy_start, b.busy_end, b.price_inr, b.status,
            b.created_at,
            s.name AS supplier_name, s.rating AS supplier_rating,
            v.type AS vehicle_type, v.seats AS vehicle_seats, v.large_bags AS vehicle_large_bags, v.small_bags AS vehicle_small_bags,
            r.traveler_name, r.airport_code, r.city, r.area, r.passengers, r.large_bags, r.small_bags,
            f.airline, f.flight_number, f.from_airport, f.arrival_local,
            h.hotel_id, h.name AS hotel_name, h.city AS hotel_city, h.area AS hotel_area,
            ro.drive_minutes, ro.distance_km
        FROM bookings b
        JOIN suppliers s ON b.supplier_id = s.supplier_id
        JOIN vehicles v ON b.vehicle_id = v.vehicle_id
        JOIN ride_requests r ON b.request_id = r.request_id
        JOIN flights f ON b.flight_id = f.flight_id
        JOIN hotels h ON r.hotel_id = h.hotel_id
        JOIN routes ro ON ro.airport = r.airport_code AND ro.city = r.city AND ro.area = r.area
        WHERE b.booking_number = ? AND b.is_active = 1
        """,
        (booking_number,),
    )
    row = cur.fetchone()
    if not row:
        return None
    return dict(row)


def get_bookings_for_supplier(conn: sqlite3.Connection, supplier_id: str) -> list[dict[str, Any]]:
    """Retrieve all confirmed bookings assigned to a specific taxi company."""
    cur = conn.cursor()
    cur.execute(
        """
        SELECT 
            b.booking_number, b.request_id, b.offer_id, b.supplier_id, b.vehicle_id,
            b.flight_id, b.pickup_local, b.busy_start, b.busy_end, b.price_inr, b.status,
            b.created_at,
            v.type AS vehicle_type,
            r.traveler_name, r.airport_code, r.city, r.area, r.passengers,
            f.arrival_local,
            h.name AS hotel_name
        FROM bookings b
        JOIN vehicles v ON b.vehicle_id = v.vehicle_id
        JOIN ride_requests r ON b.request_id = r.request_id
        JOIN flights f ON b.flight_id = f.flight_id
        JOIN hotels h ON r.hotel_id = h.hotel_id
        WHERE b.supplier_id = ? AND b.is_active = 1
        ORDER BY b.busy_start ASC
        """,
        (supplier_id,),
    )
    return [dict(r) for r in cur.fetchall()]


def get_all_bookings(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    """Retrieve all confirmed bookings across all suppliers/travelers."""
    cur = conn.cursor()
    cur.execute(
        """
        SELECT 
            b.booking_number, b.request_id, b.offer_id, b.supplier_id, b.vehicle_id,
            b.flight_id, b.pickup_local, b.busy_start, b.busy_end, b.price_inr, b.status,
            b.created_at,
            s.name AS supplier_name, s.rating AS supplier_rating,
            v.type AS vehicle_type, v.seats AS vehicle_seats, v.large_bags AS vehicle_large_bags, v.small_bags AS vehicle_small_bags,
            r.traveler_name, r.airport_code, r.city, r.area, r.passengers, r.large_bags, r.small_bags,
            f.airline, f.flight_number, f.from_airport, f.arrival_local,
            h.hotel_id, h.name AS hotel_name, h.city AS hotel_city, h.area AS hotel_area,
            ro.drive_minutes, ro.distance_km
        FROM bookings b
        JOIN suppliers s ON b.supplier_id = s.supplier_id
        JOIN vehicles v ON b.vehicle_id = v.vehicle_id
        JOIN ride_requests r ON b.request_id = r.request_id
        JOIN flights f ON b.flight_id = f.flight_id
        JOIN hotels h ON r.hotel_id = h.hotel_id
        JOIN routes ro ON ro.airport = r.airport_code AND ro.city = r.city AND ro.area = r.area
        WHERE b.is_active = 1
        ORDER BY b.created_at DESC
        """
    )
    return [dict(r) for r in cur.fetchall()]

