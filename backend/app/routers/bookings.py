"""Bookings router for creating bookings, retrieving summary, and requesting flight changes."""

import sqlite3
from typing import Any
from fastapi import APIRouter, Depends, status

from backend.app.db.connection import get_db
from backend.app.schemas import (
    BookingResponse,
    ChangeRequestCreate,
    ChangeRequestResponse,
)
from backend.app.services.booking_service import book_offer, get_booking
from backend.app.services.change_service import (
    get_booking_changes,
    request_flight_change,
)

router = APIRouter(prefix="/api", tags=["Bookings"])


@router.post(
    "/offers/{offer_id}/book",
    response_model=BookingResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Book an open taxi offer",
)
def post_book_offer(
    offer_id: int,
    conn: sqlite3.Connection = Depends(get_db),
) -> BookingResponse:
    """Atomically books the selected offer, marks competitor offers NOT_CHOSEN, generates 10-digit number."""
    return book_offer(conn, offer_id)


@router.get(
    "/bookings/{booking_number}",
    response_model=BookingResponse,
    summary="Get confirmed booking details by 10-digit number",
)
def get_booking_by_number_endpoint(
    booking_number: str,
    conn: sqlite3.Connection = Depends(get_db),
) -> BookingResponse:
    """Retrieve booking summary by 10-digit booking number; returns 404 if not found."""
    return get_booking(conn, booking_number)


@router.post(
    "/bookings/{booking_number}/changes",
    response_model=ChangeRequestResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Request flight / pickup time change on a confirmed booking",
)
def post_booking_change(
    booking_number: str,
    payload: ChangeRequestCreate,
    conn: sqlite3.Connection = Depends(get_db),
) -> ChangeRequestResponse:
    """Submit a flight change request validated against pickup window and same-airport flight."""
    return request_flight_change(
        conn,
        booking_number,
        payload.new_flight_id,
        payload.new_pickup_local,
    )


@router.get(
    "/bookings/{booking_number}/changes",
    response_model=list[ChangeRequestResponse],
    summary="Get all change requests for a confirmed booking",
)
def get_booking_changes_endpoint(
    booking_number: str,
    conn: sqlite3.Connection = Depends(get_db),
) -> list[ChangeRequestResponse]:
    """List historical and active flight changes for this booking."""
    return get_booking_changes(conn, booking_number)
