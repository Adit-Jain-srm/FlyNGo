"""Catalog router for airports, flights, hotels, pricing quotes, and vehicle suitability."""

import sqlite3
from fastapi import APIRouter, Depends, Query

from backend.app.db.connection import get_db
from backend.app.repositories import catalog_repo
from backend.app.schemas import (
    AirportResponse,
    CarTypeSuitabilityResponse,
    FlightResponse,
    HotelResponse,
    RouteQuoteResponse,
)
from backend.app.services.quote_service import get_route_quote, get_suitable_car_types

router = APIRouter(prefix="/api", tags=["Catalog"])


@router.get(
    "/airports",
    response_model=list[AirportResponse],
    summary="Get all arrival destination airports",
)
def get_airports(conn: sqlite3.Connection = Depends(get_db)) -> list[AirportResponse]:
    """Retrieve the 5 destination airports receiving flights (NRT, HND, KIX, DXB, AUH)."""
    rows = catalog_repo.get_arrival_airports(conn)
    return [AirportResponse(**dict(r)) for r in rows]


@router.get(
    "/flights",
    response_model=list[FlightResponse],
    summary="Get arrival flights for an airport and date",
)
def get_flights(
    airport: str = Query(..., description="Arrival airport code (e.g. NRT)"),
    date: str = Query(..., description="Arrival date YYYY-MM-DD (e.g. 2027-04-10)"),
    conn: sqlite3.Connection = Depends(get_db),
) -> list[FlightResponse]:
    """Query flights landing at the specified airport on the specified date."""
    rows = catalog_repo.get_flights(conn, airport.upper(), date)
    return [FlightResponse(**dict(r)) for r in rows]


@router.get(
    "/hotels",
    response_model=list[HotelResponse],
    summary="Search hotels in cities served by an airport",
)
def get_hotels(
    airport: str = Query(..., description="Arrival airport code (e.g. NRT)"),
    q: str | None = Query(default=None, description="Optional search text for hotel name, area, or city"),
    conn: sqlite3.Connection = Depends(get_db),
) -> list[HotelResponse]:
    """Retrieve hotels reachable from the given airport. q matches name, area, or city."""
    rows = catalog_repo.get_hotels_by_airport(conn, airport.upper(), q)
    return [HotelResponse(**dict(r)) for r in rows]


@router.get(
    "/quote",
    response_model=RouteQuoteResponse,
    summary="Get suggested price range and recommended pickup window for a route",
)
def get_quote(
    flight_id: str = Query(..., description="Flight ID (e.g. FL-401)"),
    hotel_id: str = Query(..., description="Hotel ID (e.g. HTL-TYO-004)"),
    conn: sqlite3.Connection = Depends(get_db),
) -> RouteQuoteResponse:
    """Calculate distance, drive time, price range, and pickup window."""
    return get_route_quote(conn, flight_id, hotel_id)


@router.get(
    "/car-types",
    response_model=list[CarTypeSuitabilityResponse],
    summary="Get car types capable of fitting the passenger party and luggage",
)
def get_car_types(
    pax: int = Query(..., ge=1, description="Total passenger count (adults + children)"),
    large: int = Query(default=0, ge=0, description="Large / check-in bags"),
    small: int = Query(default=0, ge=0, description="Small / cabin bags"),
    conn: sqlite3.Connection = Depends(get_db),
) -> list[CarTypeSuitabilityResponse]:
    """Filter vehicle types in fleet that fit the group's seats and luggage constraints."""
    return get_suitable_car_types(conn, pax, large, small)
