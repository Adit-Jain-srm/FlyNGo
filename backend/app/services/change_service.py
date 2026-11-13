"""Change service business logic and orchestration for Milestone M7."""

import sqlite3
from typing import Any, Optional

from backend.app.repositories import change_repo


def request_flight_change(
    conn: sqlite3.Connection,
    booking_number: str,
    new_flight_id: str,
    new_pickup_local: Optional[str] = None,
) -> dict[str, Any]:
    """Submit a new flight change request for an existing confirmed booking."""
    return change_repo.create_change_request(conn, booking_number, new_flight_id, new_pickup_local)


def get_booking_changes(conn: sqlite3.Connection, booking_number: str) -> list[dict[str, Any]]:
    """List all change requests for a given booking."""
    return change_repo.get_changes_for_booking(conn, booking_number)


def get_supplier_changes(conn: sqlite3.Connection, supplier_id: str) -> list[dict[str, Any]]:
    """List all change requests assigned to a supplier."""
    return change_repo.get_changes_for_supplier(conn, supplier_id)


def process_change_decision(
    conn: sqlite3.Connection,
    change_id: int,
    decision: str,  # 'ACCEPTED' or 'REJECTED'
    reject_reason: Optional[str] = None,
) -> dict[str, Any]:
    """Process supplier acceptance or rejection of a flight change request."""
    return change_repo.decide_change_request(conn, change_id, decision, reject_reason)
