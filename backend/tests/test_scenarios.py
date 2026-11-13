"""Happy and unhappy paths for M1–M7 that the earlier tests did not cover.

Each test uses a fresh database. The Menon trip is FL-401 to HTL-TYO-004:
landing 10:30, route drive 90 minutes, price ₹10,200–₹16,800.
"""

import sqlite3

from fastapi.testclient import TestClient


MENON = {
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


def _post_menon(client: TestClient, **overrides: object) -> dict:
    body = {**MENON, **overrides}
    response = client.post("/api/requests", json=body)
    assert response.status_code == 201, response.text
    return response.json()


def _assign(client: TestClient, request_id: str, supplier_id: str, vehicle_id: str, price: int):
    return client.post(
        f"/api/requests/{request_id}/offers",
        json={"supplier_id": supplier_id, "vehicle_id": vehicle_id, "price_inr": price},
    )


def _book_sakura(client: TestClient) -> dict:
    created = _post_menon(client)
    offer = _assign(client, created["request_id"], "TX-JP-01", "SC-3", 12500)
    assert offer.status_code == 201, offer.text
    booked = client.post(f"/api/offers/{offer.json()['offer_id']}/book")
    assert booked.status_code == 201, booked.text
    return booked.json()


def test_happy_price_and_pickup_boundaries(client: TestClient) -> None:
    """M1: the minimum price and a pickup exactly 60 minutes after landing are accepted."""
    created = _post_menon(client, price_inr=10200, pickup_local="2027-04-10T11:30")
    assert created["price_inr"] == 10200
    assert created["pickup_local"] == "2027-04-10T11:30"


def test_happy_omitted_pickup_defaults_to_landing_plus_60(client: TestClient) -> None:
    """M1: no pickup time means landing + 60 minutes."""
    payload = {k: v for k, v in MENON.items() if k != "pickup_local"}
    response = client.post("/api/requests", json=payload)
    assert response.status_code == 201, response.text
    assert response.json()["pickup_local"] == "2027-04-10T11:30"


def test_happy_infant_counts_as_a_passenger(client: TestClient) -> None:
    """R1/R5: a child aged 0 needs a seat."""
    created = _post_menon(client, adults=1, child_ages=[0], large_bags=1, small_bags=1, price_inr=11000)
    assert created["passengers"] == 2
    assert created["children"][0]["age"] == 0


def test_unhappy_unknown_flight_and_hotel(client: TestClient) -> None:
    """R1: a flight or hotel that is not in the catalog is not found."""
    missing_flight = client.post("/api/requests", json={**MENON, "flight_id": "FL-NOPE"})
    assert missing_flight.status_code == 404
    assert "FL-NOPE" in missing_flight.json()["message"]

    missing_hotel = client.post("/api/requests", json={**MENON, "hotel_id": "HTL-NOPE"})
    assert missing_hotel.status_code == 404
    assert "HTL-NOPE" in missing_hotel.json()["message"]


def test_unhappy_price_above_maximum(client: TestClient) -> None:
    """R3: one rupee over the maximum is refused and the range is shown."""
    response = client.post("/api/requests", json={**MENON, "price_inr": 16801})
    assert response.status_code == 422
    body = response.json()
    assert body["rule"] == "R3"
    assert body["allowed"] == {"min": 10200, "max": 16800}


def test_unhappy_negative_bags_and_bad_child_age(client: TestClient) -> None:
    """R1: negative bags and a child aged 18 are refused."""
    bags = client.post("/api/requests", json={**MENON, "large_bags": -1})
    assert bags.status_code == 422

    age = client.post("/api/requests", json={**MENON, "child_ages": [18]})
    assert age.status_code == 422
    assert age.json()["rule"] == "R1"
    assert age.json()["field"] == "child_ages"


def test_unhappy_price_at_maximum_is_allowed(client: TestClient) -> None:
    """R3: the maximum itself is inside the range."""
    created = _post_menon(client, price_inr=16800)
    assert created["price_inr"] == 16800


def test_unhappy_car_from_another_supplier(client: TestClient) -> None:
    """R7: Sakura cannot assign Edo's car."""
    created = _post_menon(client)
    response = _assign(client, created["request_id"], "TX-JP-01", "EP-1", 12000)
    assert response.status_code == 422
    assert response.json()["rule"] == "R7"


def test_unhappy_wrong_car_type_on_seeded_request(client: TestClient) -> None:
    """G2: REQ-0002 asks for a sedan, so an SUV is refused."""
    response = _assign(client, "REQ-0002", "TX-JP-05", "KA-2", 9000)
    assert response.status_code == 422
    assert response.json()["rule"] == "R5"
    assert "SEDAN" in response.json()["message"]


def test_booking_busy_window_covers_the_return_drive(client: TestClient, temp_db: sqlite3.Connection) -> None:
    """R6: Menon's 90-minute drive keeps the car busy until 14:30, not 13:00."""
    booking = _book_sakura(client)
    assert booking["busy_start"] == "2027-04-10T11:30"
    assert booking["busy_end"] == "2027-04-10T14:30"

    row = temp_db.execute(
        "SELECT busy_start, busy_end FROM bookings WHERE booking_number = ?",
        (booking["booking_number"],),
    ).fetchone()
    assert row["busy_start"] == "2027-04-10T11:30"
    assert row["busy_end"] == "2027-04-10T14:30"


def test_m6_second_booking_of_the_same_car_overlaps(client: TestClient) -> None:
    """M6: two open offers for one car; booking the second is refused after the first is confirmed."""
    first = _post_menon(client, traveler_name="First")
    second = _post_menon(client, traveler_name="Second")
    offer_a = _assign(client, first["request_id"], "TX-JP-01", "SC-3", 12000)
    offer_b = _assign(client, second["request_id"], "TX-JP-01", "SC-3", 13000)
    assert offer_a.status_code == 201
    assert offer_b.status_code == 201

    booked = client.post(f"/api/offers/{offer_a.json()['offer_id']}/book")
    assert booked.status_code == 201

    overlap = client.post(f"/api/offers/{offer_b.json()['offer_id']}/book")
    assert overlap.status_code == 409
    assert "no longer available" in overlap.json()["message"]


def test_happy_touching_busy_windows_do_not_overlap(client: TestClient) -> None:
    """R6: a ride that starts exactly when the previous busy window ends is allowed."""
    _book_sakura(client)
    later = _post_menon(client, traveler_name="Later", pickup_local="2027-04-10T14:30")
    offer = _assign(client, later["request_id"], "TX-JP-01", "SC-3", 12000)
    assert offer.status_code == 201, offer.text
    booked = client.post(f"/api/offers/{offer.json()['offer_id']}/book")
    assert booked.status_code == 201, booked.text
    assert booked.json()["busy_start"] == "2027-04-10T14:30"
    assert booked.json()["busy_end"] == "2027-04-10T17:30"


def test_unhappy_rejected_offer_cannot_be_booked(client: TestClient) -> None:
    """R8: a rejected taxi stays rejected."""
    created = _post_menon(client)
    offer = _assign(client, created["request_id"], "TX-JP-01", "SC-3", 12000)
    offer_id = offer.json()["offer_id"]
    rejected = client.post(f"/api/offers/{offer_id}/reject")
    assert rejected.status_code == 200
    booked = client.post(f"/api/offers/{offer_id}/book")
    assert booked.status_code == 409


def test_happy_pickup_only_change(client: TestClient) -> None:
    """M7: a new pickup time, with no new flight, is accepted and the flight stays."""
    booking = _book_sakura(client)
    number = booking["booking_number"]
    change = client.post(
        f"/api/bookings/{number}/changes",
        json={"new_pickup_local": "2027-04-10T12:00"},
    )
    assert change.status_code == 201, change.text
    assert change.json()["new_flight_id"] == "FL-401"
    assert change.json()["status"] == "WAITING"

    accepted = client.post(f"/api/changes/{change.json()['change_id']}/accept")
    assert accepted.status_code == 200
    assert accepted.json()["status"] == "ACCEPTED"

    summary = client.get(f"/api/bookings/{number}").json()
    assert summary["flight_id"] == "FL-401"
    assert summary["pickup_local"] == "2027-04-10T12:00"
    assert summary["busy_end"] == "2027-04-10T15:00"


def test_change_to_another_arrival_airport_is_allowed(client: TestClient) -> None:
    """R9: a new flight is accepted when the pickup is valid and the same car is free."""
    booking = _book_sakura(client)
    number = booking["booking_number"]
    response = client.post(
        f"/api/bookings/{number}/changes",
        json={"new_flight_id": "FL-731"},
    )
    assert response.status_code == 201, response.text
    accepted = client.post(f"/api/changes/{response.json()['change_id']}/accept")
    assert accepted.status_code == 200, accepted.text
    assert accepted.json()["status"] == "ACCEPTED"
    summary = client.get(f"/api/bookings/{number}").json()
    assert summary["flight_id"] == "FL-731"


def test_unhappy_empty_change_is_refused(client: TestClient) -> None:
    """M7: a change with neither a flight nor a pickup is refused."""
    booking = _book_sakura(client)
    response = client.post(f"/api/bookings/{booking['booking_number']}/changes", json={})
    assert response.status_code == 422


def test_unhappy_supplier_closed_at_pickup(client: TestClient) -> None:
    """R4: Edo closes at 22:00, so a 22:30 pickup is refused."""
    created = _post_menon(client, pickup_local="2027-04-10T22:30")
    response = _assign(client, created["request_id"], "TX-JP-03", "EP-1", 12000)
    assert response.status_code == 422
    assert response.json()["rule"] == "R4"
    assert "closed" in response.json()["message"].lower()
