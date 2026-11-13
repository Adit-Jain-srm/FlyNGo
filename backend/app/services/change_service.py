"""Change service business logic and orchestration for Milestone M7."""

import sqlite3
from typing import Any, Optional

from backend.app.log import get_logger
from backend.app.repositories import change_repo


def request_flight_change(
    conn: sqlite3.Connection,
    booking_number: str,
    new_flight_id: Optional[str],
    new_pickup_local: Optional[str] = None,
) -> dict[str, Any]:
    """Submit a new flight change request for an existing confirmed booking."""
    created = change_repo.create_change_request(conn, booking_number, new_flight_id, new_pickup_local)
    get_logger().info(
        "change requested id=%s booking=%s flight=%s pickup=%s",
        created["change_id"],
        created["booking_number"],
        created["new_flight_id"],
        created["new_pickup_local"],
    )
    return created


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
    decided = change_repo.decide_change_request(conn, change_id, decision, reject_reason)
    outcome = decided.get("status")
    if outcome == "ACCEPTED":
        get_logger().info(
            "change accepted id=%s booking=%s flight=%s pickup=%s",
            decided["change_id"],
            decided["booking_number"],
            decided["new_flight_id"],
            decided["new_pickup_local"],
        )
    else:
        get_logger().info(
            "change rejected id=%s booking=%s status=%s reason=%s",
            decided["change_id"],
            decided["booking_number"],
            outcome,
            decided.get("reason") or "-",
        )
    return decided
