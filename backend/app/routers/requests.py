"""Requests router for posting and querying ride requests."""

import sqlite3
from fastapi import APIRouter, Depends, Query, status

from backend.app.db.connection import get_db
from backend.app.schemas import RideRequestCreate, RideRequestResponse
from backend.app.services.request_service import (
    create_new_request,
    get_request_details,
    list_all_requests,
)

router = APIRouter(prefix="/api/requests", tags=["Requests"])


@router.post(
    "",
    response_model=RideRequestResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new ride request",
)
def post_request(
    data: RideRequestCreate,
    conn: sqlite3.Connection = Depends(get_db),
) -> RideRequestResponse:
    """Create a ride request enforcing arrival airport serving hotel, pickup window, and route price range."""
    return create_new_request(conn, data)


@router.get(
    "",
    response_model=list[RideRequestResponse],
    summary="List all ride requests",
)
def get_requests(
    status_filter: str | None = Query(default=None, alias="status", description="Filter by status (OPEN or BOOKED)"),
    conn: sqlite3.Connection = Depends(get_db),
) -> list[RideRequestResponse]:
    """Retrieve all active ride requests."""
    return list_all_requests(conn, status_filter)


@router.get(
    "/{request_id}",
    response_model=RideRequestResponse,
    summary="Get single ride request details",
)
def get_request(
    request_id: str,
    conn: sqlite3.Connection = Depends(get_db),
) -> RideRequestResponse:
    """Retrieve detailed information for a specific ride request by ID."""
    return get_request_details(conn, request_id)
