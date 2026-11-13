"""Integration tests for catalog, quote, car-types, and ride request APIs."""

import pytest
from fastapi.testclient import TestClient


def test_catalog_airports(client: TestClient) -> None:
    """GET /api/airports returns only the 5 destination airports receiving flights."""
    response = client.get("/api/airports")
    assert response.status_code == 200
    airports = response.json()
    assert len(airports) == 5
    codes = {ap["code"] for ap in airports}
    assert codes == {"NRT", "HND", "KIX", "DXB", "AUH"}


def test_airport_search_matches_name_code_and_city(client: TestClient) -> None:
    """Search finds Zayed by name, code, or city, and a wildcard is not every airport."""
    by_name = client.get("/api/airports?q=zayed")
    assert by_name.status_code == 200
    assert [airport["code"] for airport in by_name.json()] == ["AUH"]

    by_code = client.get("/api/airports?q=auh")
    assert [airport["code"] for airport in by_code.json()] == ["AUH"]

    by_city = client.get("/api/airports?q=abu dhabi")
    assert [airport["code"] for airport in by_city.json()] == ["AUH"]

    assert client.get("/api/airports?q=%").json() == []


def test_catalog_flights(client: TestClient) -> None:
    """GET /api/flights returns flights for airport and arrival date."""
    response = client.get("/api/flights?airport=NRT&date=2027-04-10")
    assert response.status_code == 200
    flights = response.json()
    assert len(flights) > 0
    flight_ids = [f["flight_id"] for f in flights]
    assert "FL-401" in flight_ids

    fl_401 = next(f for f in flights if f["flight_id"] == "FL-401")
    assert fl_401["from_airport"] == "BLR"
    assert fl_401["to_airport"] == "NRT"
    assert fl_401["arrival_local"] == "2027-04-10T10:30"


def test_flight_search_stays_on_the_chosen_airport_and_date(client: TestClient) -> None:
    """Search matches airline, number, or origin without leaving the selected day."""
    by_airline = client.get("/api/flights?airport=NRT&date=2027-04-10&q=airveda")
    assert by_airline.status_code == 200
    assert any(flight["flight_id"] == "FL-401" for flight in by_airline.json())

    by_number = client.get("/api/flights?airport=NRT&date=2027-04-10&q=520")
    assert any(flight["flight_id"] == "FL-401" for flight in by_number.json())

    by_origin = client.get("/api/flights?airport=NRT&date=2027-04-10&q=BLR")
    assert by_origin.json()
    assert all(flight["from_airport"] == "BLR" for flight in by_origin.json())

    other_day = client.get("/api/flights?airport=NRT&date=2027-04-11&q=FL-401")
    assert other_day.json() == []
    assert client.get("/api/flights?airport=NRT&date=2027-04-10&q=%").json() == []


def test_catalog_hotels(client: TestClient) -> None:
    """GET /api/hotels returns hotels in cities served by the arrival airport."""
    response = client.get("/api/hotels?airport=NRT&q=Ueno")
    assert response.status_code == 200
    hotels = response.json()
    assert len(hotels) > 0
    hotel_ids = [h["hotel_id"] for h in hotels]
    assert "HTL-TYO-004" in hotel_ids

    htl = next(h for h in hotels if h["hotel_id"] == "HTL-TYO-004")
    assert htl["city"] == "Tokyo"
    assert htl["area"] == "Ueno"


def test_hotel_search_matches_name_city_and_rejects_other_airports(client: TestClient) -> None:
    """Search matches a word inside the name or the city, and stays on that airport."""
    by_name = client.get("/api/hotels?airport=NRT&q=garden")
    assert by_name.status_code == 200
    assert any(h["hotel_id"] == "HTL-TYO-004" for h in by_name.json())

    by_city = client.get("/api/hotels?airport=NRT&q=tokyo")
    assert by_city.status_code == 200
    assert by_city.json()
    assert all(h["city"] == "Tokyo" for h in by_city.json())

    other_airport = client.get("/api/hotels?airport=DXB&q=Ueno")
    assert other_airport.status_code == 200
    assert other_airport.json() == []

    wildcard = client.get("/api/hotels?airport=NRT&q=%")
    assert wildcard.status_code == 200
    assert wildcard.json() == []


def test_quote_endpoint(client: TestClient) -> None:
    """GET /api/quote computes distance, drive time, and price range."""
    response = client.get("/api/quote?flight_id=FL-401&hotel_id=HTL-TYO-004")
    assert response.status_code == 200
    quote = response.json()
    assert quote["airport"] == "NRT"
    assert quote["city"] == "Tokyo"
    assert quote["area"] == "Ueno"
    assert quote["distance_km"] == 73.3
    assert quote["drive_minutes"] == 90
    assert quote["price_min_inr"] == 10200
    assert quote["price_max_inr"] == 16800
    assert quote["recommended_pickup_local"] == "2027-04-10T11:30"


def test_car_types_suitability(client: TestClient) -> None:
    """GET /api/car-types returns only types that fit the party (G2)."""
    # 7 passengers -> only SUV and BUS fit
    response = client.get("/api/car-types?pax=7&large=3&small=2")
    assert response.status_code == 200
    types = [ct["type"] for ct in response.json()]
    assert "SUV" in types
    assert "BUS" in types
    assert "SEDAN" not in types
    assert "HATCHBACK" not in types


def test_post_request_unhappy_price_r3(client: TestClient) -> None:
    """POST /api/requests refuses price outside range with 422 and R3 details."""
    payload = {
        "traveler_name": "Menon Family",
        "flight_id": "FL-401",
        "hotel_id": "HTL-TYO-004",
        "adults": 2,
        "child_ages": [6],
        "large_bags": 3,
        "small_bags": 2,
        "pickup_local": "2027-04-10T11:30",
        "price_inr": 9000,  # Below minimum ₹10,200
    }
    response = client.post("/api/requests", json=payload)
    assert response.status_code == 422
    err = response.json()
    assert err["rule"] == "R3"
    assert err["field"] == "price_inr"
    assert err["allowed"] == {"min": 10200, "max": 16800}


def test_post_request_happy_menon_req0004(client: TestClient) -> None:
    """POST /api/requests successfully creates REQ-0004 for Menon family."""
    payload = {
        "traveler_name": "Menon Family",
        "flight_id": "FL-401",
        "hotel_id": "HTL-TYO-004",
        "adults": 2,
        "child_ages": [6],
        "large_bags": 3,
        "small_bags": 2,
        "pickup_local": "2027-04-10T11:30",
        "price_inr": 12000,
    }
    response = client.post("/api/requests", json=payload)
    assert response.status_code == 201
    created = response.json()
    assert created["request_id"] == "REQ-0004"
    assert created["status"] == "OPEN"
    assert created["passengers"] == 3
    assert created["airport_code"] == "NRT"
    assert created["city"] == "Tokyo"
    assert created["area"] == "Ueno"
    assert len(created["children"]) == 1
    assert created["children"][0]["age"] == 6

    # Verify retrieval by ID
    get_res = client.get("/api/requests/REQ-0004")
    assert get_res.status_code == 200
    fetched = get_res.json()
    assert fetched["request_id"] == "REQ-0004"
    assert fetched["hotel_name"] == "Ueno Garden Inn"
    assert fetched["price_min_inr"] == 10200


def test_post_request_unhappy_r1_city_mismatch(client: TestClient) -> None:
    """POST /api/requests refuses hotel in city not served by arrival airport."""
    payload = {
        "traveler_name": "Tester",
        "flight_id": "FL-401",        # Lands at NRT (Tokyo)
        "hotel_id": "HTL-OSA-001",    # Located in Osaka (Namba)
        "adults": 1,
        "price_inr": 10000,
    }
    response = client.post("/api/requests", json=payload)
    assert response.status_code == 422
    err = response.json()
    assert err["rule"] == "R1"
    assert err["field"] == "hotel_id"


def test_post_request_unhappy_r2_pickup_too_early(client: TestClient) -> None:
    """POST /api/requests refuses pickup earlier than landing + 60m."""
    payload = {
        "traveler_name": "Tester",
        "flight_id": "FL-401",        # Lands at 10:30
        "hotel_id": "HTL-TYO-004",
        "adults": 1,
        "pickup_local": "2027-04-10T10:45",  # 15m after landing
        "price_inr": 12000,
    }
    response = client.post("/api/requests", json=payload)
    assert response.status_code == 422
    err = response.json()
    assert err["rule"] == "R2"
    assert err["field"] == "pickup_local"
