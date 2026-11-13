"""Offers router for creating, listing, and rejecting vehicle offers."""

import sqlite3
from typing import Any
from fastapi import APIRouter, Depends, Path, status

from backend.app.db.connection import get_db
from backend.app.errors import NotFoundException
from backend.app.repositories import offer_repo
from backend.app.schemas import OfferCreatePayload, OfferResponse
from backend.app.services.offer_service import (
    create_supplier_offer,
    get_request_offers_and_status,
)

router = APIRouter(prefix="/api", tags=["Offers"])


@router.post(
    "/requests/{request_id}/offers",
    response_model=OfferResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Assign a car with a price to a request",
)
def post_offer(
    request_id: str,
    payload: OfferCreatePayload,
    conn: sqlite3.Connection = Depends(get_db),
) -> OfferResponse:
    """Supplier assigns one of its vehicles with a price; validates eligibility and price range."""
    return create_supplier_offer(conn, request_id, payload)


@router.get(
    "/requests/{request_id}/offers",
    response_model=dict[str, Any],
    summary="Get offers and eligibility status for a request",
)
def get_request_offers(
    request_id: str,
    conn: sqlite3.Connection = Depends(get_db),
) -> dict[str, Any]:
    """Retrieve active offers for a request and availability status if no offers exist."""
    return get_request_offers_and_status(conn, request_id)


@router.post(
    "/offers/{offer_id}/reject",
    response_model=dict[str, str],
    summary="Traveler rejects an assigned taxi offer",
)
def reject_offer_endpoint(
    offer_id: int,
    conn: sqlite3.Connection = Depends(get_db),
) -> dict[str, str]:
    """Mark an offer as REJECTED so it can no longer be booked."""
    success = offer_repo.reject_offer(conn, offer_id)
    if not success:
        raise NotFoundException(f"Open offer #{offer_id} not found or already closed.")
    return {"status": "REJECTED", "message": f"Offer #{offer_id} has been rejected."}
