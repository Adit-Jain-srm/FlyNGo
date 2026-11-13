"""Changes router for supplier decisions on flight changes."""

import sqlite3
from typing import Any
from fastapi import APIRouter, Depends, status

from backend.app.db.connection import get_db
from backend.app.schemas import ChangeDecisionPayload, ChangeRequestResponse
from backend.app.services.change_service import process_change_decision

router = APIRouter(prefix="/api/changes", tags=["Changes"])


@router.post(
    "/{change_id}/accept",
    response_model=ChangeRequestResponse,
    summary="Supplier accepts flight change",
)
def accept_change_endpoint(
    change_id: int,
    conn: sqlite3.Connection = Depends(get_db),
) -> ChangeRequestResponse:
    """Supplier accepts flight change.
    
    Re-checks pickup window and vehicle availability:
    - If free, updates booking and request pickup times.
    - If busy, auto-rejects with reason and leaves original booking unchanged.
    """
    return process_change_decision(conn, change_id, decision="ACCEPTED")


@router.post(
    "/{change_id}/reject",
    response_model=ChangeRequestResponse,
    summary="Supplier rejects flight change",
)
def reject_change_endpoint(
    change_id: int,
    payload: ChangeDecisionPayload | None = None,
    conn: sqlite3.Connection = Depends(get_db),
) -> ChangeRequestResponse:
    """Supplier rejects flight change with optional reason. Original booking is unchanged."""
    reason = payload.reason if payload else None
    return process_change_decision(conn, change_id, decision="REJECTED", reject_reason=reason)
