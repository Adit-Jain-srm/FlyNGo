"""Suppliers router for supplier profiles, fleet cars, and dashboards."""

import sqlite3
from typing import Any
from fastapi import APIRouter, Depends, Path

from backend.app.db.connection import get_db
from backend.app.errors import NotFoundException
from backend.app.repositories import offer_repo, supplier_repo
from backend.app.schemas import (
    CarAdvisoryResponse,
    OfferResponse,
    RideRequestResponse,
    SupplierResponse,
)
from backend.app.services.offer_service import (
    get_car_advisories_for_request,
    get_requests_for_supplier,
)

router = APIRouter(prefix="/api/suppliers", tags=["Suppliers"])


@router.get(
    "",
    response_model=list[SupplierResponse],
    summary="Get all registered taxi suppliers",
)
def list_suppliers(conn: sqlite3.Connection = Depends(get_db)) -> list[SupplierResponse]:
    """Retrieve all 11 taxi companies with their service hours, airports, and areas."""
    rows = supplier_repo.get_all_suppliers(conn)
    results = []
    for r in rows:
        sid = r["supplier_id"]
        airports = supplier_repo.get_supplier_airports(conn, sid)
        areas = supplier_repo.get_supplier_areas(conn, sid)
        results.append(
            SupplierResponse(
                supplier_id=sid,
                name=r["name"],
                service_from=r["service_from"],
                service_until=r["service_until"],
                rating=r["rating"],
                airports=airports,
                areas=areas,
            )
        )
    return results


@router.get(
    "/{supplier_id}",
    response_model=SupplierResponse,
    summary="Get single supplier profile",
)
def get_supplier(
    supplier_id: str,
    conn: sqlite3.Connection = Depends(get_db),
) -> SupplierResponse:
    """Retrieve a single taxi company profile."""
    r = supplier_repo.get_supplier_by_id(conn, supplier_id)
    if not r:
        raise NotFoundException(f"Supplier {supplier_id} not found.")

    airports = supplier_repo.get_supplier_airports(conn, supplier_id)
    areas = supplier_repo.get_supplier_areas(conn, supplier_id)
    return SupplierResponse(
        supplier_id=supplier_id,
        name=r["name"],
        service_from=r["service_from"],
        service_until=r["service_until"],
        rating=r["rating"],
        airports=airports,
        areas=areas,
    )


@router.get(
    "/{supplier_id}/requests",
    response_model=list[RideRequestResponse],
    summary="B.2 Supplier dashboard: open requests this supplier can serve",
)
def get_dashboard_requests(
    supplier_id: str,
    conn: sqlite3.Connection = Depends(get_db),
) -> list[RideRequestResponse]:
    """Retrieve open requests matching airport, area, service window, and fleet availability."""
    return get_requests_for_supplier(conn, supplier_id)


@router.get(
    "/{supplier_id}/requests/{request_id}/cars",
    response_model=list[CarAdvisoryResponse],
    summary="Evaluate supplier fleet cars against a request and get advisory badges",
)
def get_cars_for_request(
    supplier_id: str,
    request_id: str,
    conn: sqlite3.Connection = Depends(get_db),
) -> list[CarAdvisoryResponse]:
    """Returns all cars of the supplier with status badges (Fits and free, Busy until ..., Too small)."""
    return get_car_advisories_for_request(conn, supplier_id, request_id)


@router.get(
    "/{supplier_id}/offers",
    response_model=list[OfferResponse],
    summary="Get offers submitted by this supplier",
)
def get_supplier_offers(
    supplier_id: str,
    conn: sqlite3.Connection = Depends(get_db),
) -> list[OfferResponse]:
    """Retrieve all active offers made by this supplier."""
    rows = offer_repo.get_offers_for_supplier(conn, supplier_id)
    return [OfferResponse(**dict(r)) for r in rows]


@router.get(
    "/{supplier_id}/bookings",
    response_model=list[dict[str, Any]],
    summary="Get confirmed bookings for this supplier",
)
def get_supplier_bookings(
    supplier_id: str,
    conn: sqlite3.Connection = Depends(get_db),
) -> list[dict[str, Any]]:
    """Retrieve all confirmed bookings assigned to this supplier."""
    rows = supplier_repo.get_supplier_bookings(conn, supplier_id)
    return [dict(r) for r in rows]


@router.get(
    "/{supplier_id}/changes",
    response_model=list[dict[str, Any]],
    summary="Get change requests for this supplier",
)
def get_supplier_changes(
    supplier_id: str,
    conn: sqlite3.Connection = Depends(get_db),
) -> list[dict[str, Any]]:
    """Retrieve flight change requests awaiting supplier decision."""
    rows = supplier_repo.get_supplier_changes(conn, supplier_id)
    return [dict(r) for r in rows]
