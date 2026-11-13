"""Quote and vehicle suitability service."""

import sqlite3

from backend.app.errors import NotFoundException, RuleViolationException
from backend.app.repositories import catalog_repo
from backend.app.schemas import CarTypeSuitabilityResponse, RouteQuoteResponse
from backend.app.services.rules import compute_pickup_window, validate_r1_request


def get_route_quote(
    conn: sqlite3.Connection,
    flight_id: str,
    hotel_id: str,
) -> RouteQuoteResponse:
    """Validate route pairing and return suggested price range and pickup times."""
    flight = catalog_repo.get_flight_by_id(conn, flight_id)
    if not flight:
        raise NotFoundException(f"Flight {flight_id} not found in catalog.")

    hotel = catalog_repo.get_hotel_by_id(conn, hotel_id)
    if not hotel:
        raise NotFoundException(f"Hotel {hotel_id} not found in catalog.")

    airport_code = flight["to_airport"]
    hotel_city = hotel["city"]
    hotel_area = hotel["area"]

    # Verify R1 constraint: Arrival airport serves hotel's city
    serves_cities = catalog_repo.get_airport_cities(conn, airport_code)
    validate_r1_request(
        arrival_airport=airport_code,
        serves_cities=serves_cities,
        hotel_city=hotel_city,
        adults=1,
        child_ages=[],
        large_bags=0,
        small_bags=0,
    )

    # Lookup route
    route = catalog_repo.get_route(conn, airport_code, hotel_city, hotel_area)
    if not route:
        raise NotFoundException(
            f"No route defined for {airport_code} to {hotel_city} ({hotel_area})."
        )

    default_p, earliest_p, latest_p = compute_pickup_window(flight["arrival_local"])

    return RouteQuoteResponse(
        airport=airport_code,
        city=hotel_city,
        area=hotel_area,
        distance_km=route["distance_km"],
        drive_minutes=route["drive_minutes"],
        price_min_inr=route["price_min_inr"],
        price_max_inr=route["price_max_inr"],
        recommended_pickup_local=default_p,
        earliest_pickup_local=earliest_p,
        latest_pickup_local=latest_p,
    )


def get_suitable_car_types(
    conn: sqlite3.Connection,
    pax: int,
    large_bags: int,
    small_bags: int,
) -> list[CarTypeSuitabilityResponse]:
    """Return only vehicle types in fleet that can fit the party and bags (G2)."""
    limits = catalog_repo.get_vehicle_type_limits(conn)
    results = []

    for row in limits:
        # Check if type has capacity
        if (
            row["max_seats"] >= pax
            and row["max_large_bags"] >= large_bags
            and row["max_small_bags"] >= small_bags
        ):
            results.append(
                CarTypeSuitabilityResponse(
                    type=row["type"],
                    max_seats=row["max_seats"],
                    max_large_bags=row["max_large_bags"],
                    max_small_bags=row["max_small_bags"],
                    available_fleet_count=row["available_fleet_count"],
                )
            )

    return results
