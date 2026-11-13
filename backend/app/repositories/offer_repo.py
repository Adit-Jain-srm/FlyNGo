"""Offer repository for managing assigned taxi offers."""

import sqlite3
from typing import Any


def create_offer(
    conn: sqlite3.Connection,
    request_id: str,
    supplier_id: str,
    vehicle_id: str,
    price_inr: int,
) -> int:
    """Insert a new vehicle offer into the offers table."""
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO offers (request_id, supplier_id, vehicle_id, price_inr, status, is_active, updated_at)
        VALUES (?, ?, ?, ?, 'OPEN', 1, CURRENT_TIMESTAMP);
        """,
        (request_id, supplier_id, vehicle_id, price_inr),
    )
    return cur.lastrowid


def get_offer_by_id(conn: sqlite3.Connection, offer_id: int) -> dict[str, Any] | None:
    """Retrieve full details of an offer including supplier and vehicle metadata."""
    query = """
        SELECT o.*,
               s.name AS supplier_name, s.rating AS supplier_rating,
               v.type AS vehicle_type, v.seats AS vehicle_seats,
               v.large_bags AS vehicle_large_bags, v.small_bags AS vehicle_small_bags
        FROM offers o
        JOIN suppliers s ON s.supplier_id = o.supplier_id AND s.is_active = 1
        JOIN vehicles v ON v.vehicle_id = o.vehicle_id AND v.is_active = 1
        WHERE o.offer_id = ? AND o.is_active = 1;
    """
    row = conn.execute(query, (offer_id,)).fetchone()
    return dict(row) if row else None


def get_offers_for_request(conn: sqlite3.Connection, request_id: str) -> list[dict[str, Any]]:
    """Retrieve all active offers assigned to a specific ride request."""
    query = """
        SELECT o.*,
               s.name AS supplier_name, s.rating AS supplier_rating,
               v.type AS vehicle_type, v.seats AS vehicle_seats,
               v.large_bags AS vehicle_large_bags, v.small_bags AS vehicle_small_bags
        FROM offers o
        JOIN suppliers s ON s.supplier_id = o.supplier_id AND s.is_active = 1
        JOIN vehicles v ON v.vehicle_id = o.vehicle_id AND v.is_active = 1
        WHERE o.request_id = ? AND o.is_active = 1
        ORDER BY o.price_inr ASC, o.created_at ASC;
    """
    rows = conn.execute(query, (request_id,)).fetchall()
    return [dict(r) for r in rows]


def get_offers_for_supplier(conn: sqlite3.Connection, supplier_id: str) -> list[dict[str, Any]]:
    """Retrieve all offers submitted by a specific supplier."""
    query = """
        SELECT o.*,
               s.name AS supplier_name, s.rating AS supplier_rating,
               v.type AS vehicle_type, v.seats AS vehicle_seats,
               v.large_bags AS vehicle_large_bags, v.small_bags AS vehicle_small_bags,
               r.flight_id, r.hotel_id, r.city, r.area, r.pickup_local, r.passengers
        FROM offers o
        JOIN suppliers s ON s.supplier_id = o.supplier_id AND s.is_active = 1
        JOIN vehicles v ON v.vehicle_id = o.vehicle_id AND v.is_active = 1
        JOIN ride_requests r ON r.request_id = o.request_id AND r.is_active = 1
        WHERE o.supplier_id = ? AND o.is_active = 1
        ORDER BY o.created_at DESC;
    """
    rows = conn.execute(query, (supplier_id,)).fetchall()
    return [dict(r) for r in rows]


def check_existing_offer_for_car(
    conn: sqlite3.Connection,
    request_id: str,
    vehicle_id: str,
) -> bool:
    """Check if this vehicle has already been offered for this request."""
    row = conn.execute(
        """
        SELECT 1 FROM offers
        WHERE request_id = ? AND vehicle_id = ? AND is_active = 1;
        """,
        (request_id, vehicle_id),
    ).fetchone()
    return row is not None


def reject_offer(conn: sqlite3.Connection, offer_id: int) -> bool:
    """Mark an offer as REJECTED by traveler."""
    cur = conn.cursor()
    cur.execute(
        """
        UPDATE offers
        SET status = 'REJECTED', updated_at = CURRENT_TIMESTAMP
        WHERE offer_id = ? AND status = 'OPEN' AND is_active = 1;
        """,
        (offer_id,),
    )
    conn.commit()
    return cur.rowcount > 0
