"""Booking service business logic and orchestration."""

import sqlite3
from typing import Any

from backend.app.errors import NotFoundException
from backend.app.repositories import booking_repo


def book_offer(conn: sqlite3.Connection, offer_id: int) -> dict[str, Any]:
    """Atomically books an open offer and request, sets competitor offers to NOT_CHOSEN."""
    return booking_repo.create_booking_atomic(conn, offer_id)


def get_booking(conn: sqlite3.Connection, booking_number: str) -> dict[str, Any]:
    """Retrieve booking by 10-digit number; raises NotFoundException if not found."""
    booking = booking_repo.get_booking_by_number(conn, booking_number)
    if not booking:
        raise NotFoundException(f"Booking {booking_number} not found.")
    return booking


def get_supplier_bookings(conn: sqlite3.Connection, supplier_id: str) -> list[dict[str, Any]]:
    """Retrieve all confirmed bookings assigned to a supplier."""
    return booking_repo.get_bookings_for_supplier(conn, supplier_id)


def list_all_bookings(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    """Retrieve all confirmed bookings across all travelers and suppliers."""
    return booking_repo.get_all_bookings(conn)

