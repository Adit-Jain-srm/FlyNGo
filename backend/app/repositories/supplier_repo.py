"""Supplier repository for querying supplier profile, coverage, and bookings."""

import sqlite3
from typing import Any


def get_all_suppliers(conn: sqlite3.Connection) -> list[sqlite3.Row]:
    """Retrieve all active suppliers sorted by name."""
    query = """
        SELECT supplier_id, name, service_from, service_until, rating
        FROM suppliers
        WHERE is_active = 1
        ORDER BY name;
    """
    return conn.execute(query).fetchall()


def get_supplier_by_id(conn: sqlite3.Connection, supplier_id: str) -> sqlite3.Row | None:
    """Retrieve a supplier by ID."""
    query = "SELECT * FROM suppliers WHERE supplier_id = ? AND is_active = 1;"
    return conn.execute(query, (supplier_id,)).fetchone()


def get_supplier_airports(conn: sqlite3.Connection, supplier_id: str) -> list[str]:
    """Retrieve airport codes served by a supplier."""
    query = """
        SELECT airport_code FROM supplier_airports
        WHERE supplier_id = ? AND is_active = 1
        ORDER BY airport_code;
    """
    rows = conn.execute(query, (supplier_id,)).fetchall()
    return [r["airport_code"] for r in rows]


def get_supplier_areas(conn: sqlite3.Connection, supplier_id: str) -> list[dict[str, str]]:
    """Retrieve city & area pairs served by a supplier."""
    query = """
        SELECT city, area FROM supplier_areas
        WHERE supplier_id = ? AND is_active = 1
        ORDER BY city, area;
    """
    rows = conn.execute(query, (supplier_id,)).fetchall()
    return [dict(r) for r in rows]


def get_supplier_bookings(conn: sqlite3.Connection, supplier_id: str) -> list[sqlite3.Row]:
    """Retrieve confirmed bookings for this supplier."""
    query = """
        SELECT b.*, f.airline, f.flight_number, f.from_airport, f.to_airport,
               r.traveler_name, r.city, r.area, r.passengers, r.large_bags, r.small_bags,
               v.type AS vehicle_type
        FROM bookings b
        JOIN ride_requests r ON r.request_id = b.request_id AND r.is_active = 1
        JOIN flights f ON f.flight_id = b.flight_id AND f.is_active = 1
        JOIN vehicles v ON v.vehicle_id = b.vehicle_id AND v.is_active = 1
        WHERE b.supplier_id = ? AND b.is_active = 1
        ORDER BY b.pickup_local DESC;
    """
    return conn.execute(query, (supplier_id,)).fetchall()


def get_supplier_changes(conn: sqlite3.Connection, supplier_id: str) -> list[sqlite3.Row]:
    """Retrieve change requests for this supplier."""
    query = """
        SELECT c.*, b.request_id, b.vehicle_id, b.price_inr,
               r.traveler_name, r.city, r.area
        FROM change_requests c
        JOIN bookings b ON b.booking_number = c.booking_number AND b.is_active = 1
        JOIN ride_requests r ON r.request_id = b.request_id AND r.is_active = 1
        WHERE c.supplier_id = ? AND c.is_active = 1
        ORDER BY c.created_at DESC;
    """
    return conn.execute(query, (supplier_id,)).fetchall()
