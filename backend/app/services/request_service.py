"""Request management service: enforces R1-R3 rules and request lifecycle."""

import sqlite3

from backend.app.db.refdata_loader import normalize_datetime
from backend.app.errors import NotFoundException, RuleViolationException
from backend.app.log import get_logger
from backend.app.repositories import catalog_repo, request_repo
from backend.app.schemas import RideRequestCreate, RideRequestResponse
from backend.app.services.rules import (
    compute_pickup_window,
    validate_r1_request,
    validate_r2_pickup,
    validate_r3_price,
)


def create_new_request(
    conn: sqlite3.Connection,
    data: RideRequestCreate,
) -> RideRequestResponse:
    """Validate all R1, R2, R3 constraints and persist a new ride request."""
    # 1. Lookup flight
    flight = catalog_repo.get_flight_by_id(conn, data.flight_id)
    if not flight:
        raise NotFoundException(f"Flight {data.flight_id} not found in catalog.")

    # 2. Lookup hotel
    hotel = catalog_repo.get_hotel_by_id(conn, data.hotel_id)
    if not hotel:
        raise NotFoundException(f"Hotel {data.hotel_id} not found in catalog.")

    airport_code = flight["to_airport"]
    hotel_city = hotel["city"]
    hotel_area = hotel["area"]

    # 3. Rule R1: Airport serves hotel city, adults >= 1, child ages 0-17
    serves_cities = catalog_repo.get_airport_cities(conn, airport_code)
    validate_r1_request(
        arrival_airport=airport_code,
        serves_cities=serves_cities,
        hotel_city=hotel_city,
        adults=data.adults,
        child_ages=data.child_ages,
        large_bags=data.large_bags,
        small_bags=data.small_bags,
    )

    # 4. Rule R2: Pickup time window
    default_p, earliest_p, latest_p = compute_pickup_window(flight["arrival_local"])
    pickup_time = normalize_datetime(data.pickup_local) if data.pickup_local else default_p
    validate_r2_pickup(pickup_time, flight["arrival_local"])

    # 5. Rule R3: Route price bounds
    route = catalog_repo.get_route(conn, airport_code, hotel_city, hotel_area)
    if not route:
        raise RuleViolationException(
            rule="R1",
            field="hotel_id",
            message=f"No route found between arrival airport {airport_code} and hotel area {hotel_area}.",
        )

    validate_r3_price(data.price_inr, route["price_min_inr"], route["price_max_inr"])

    # 6. Generate sequential request ID and persist
    conn.execute("BEGIN TRANSACTION;")
    try:
        request_id = request_repo.get_next_request_id(conn)
        passengers = data.adults + len(data.child_ages)

        request_repo.create_ride_request(
            conn=conn,
            request_id=request_id,
            source="APP",
            traveler_name=data.traveler_name,
            flight_id=data.flight_id,
            hotel_id=data.hotel_id,
            airport_code=airport_code,
            city=hotel_city,
            area=hotel_area,
            adults=data.adults,
            passengers=passengers,
            large_bags=data.large_bags,
            small_bags=data.small_bags,
            pickup_local=pickup_time,
            car_type=data.car_type,
            price_inr=data.price_inr,
            child_ages=data.child_ages,
        )
        conn.commit()
    except Exception:
        conn.rollback()
        raise

    saved = request_repo.get_request_by_id(conn, request_id)
    if not saved:
        raise NotFoundException(f"Created request {request_id} could not be retrieved.")

    created = RideRequestResponse(**saved)
    get_logger().info(
        "request posted id=%s flight=%s hotel=%s price=%s",
        created.request_id,
        created.flight_id,
        created.hotel_id,
        created.price_inr,
    )
    return created


def get_request_details(
    conn: sqlite3.Connection,
    request_id: str,
) -> RideRequestResponse:
    """Retrieve details for a single ride request."""
    req = request_repo.get_request_by_id(conn, request_id)
    if not req:
        raise NotFoundException(f"Ride request {request_id} not found.")
    return RideRequestResponse(**req)


def list_all_requests(
    conn: sqlite3.Connection,
    status_filter: str | None = None,
) -> list[RideRequestResponse]:
    """List ride requests, optionally filtered by status."""
    rows = request_repo.list_requests(conn, status_filter)
    return [RideRequestResponse(**r) for r in rows]
