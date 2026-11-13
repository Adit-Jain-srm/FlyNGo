"""Good-to-have features G1, G2, and G4.

G5 (sort and filter) is done in the traveler offer list and does not change the API.
"""

from fastapi.testclient import TestClient


TRIP = {
    "traveler_name": "Good to have",
    "flight_id": "FL-401",
    "hotel_id": "HTL-TYO-004",
    "adults": 2,
    "child_ages": [],
    "large_bags": 2,
    "small_bags": 2,
    "pickup_local": "2027-04-10T11:30",
    "price_inr": 12000,
}


def _request(client: TestClient, **overrides: object) -> str:
    response = client.post("/api/requests", json={**TRIP, **overrides})
    assert response.status_code == 201, response.text
    return response.json()["request_id"]


def _offer(client: TestClient, request_id: str, vehicle_id: str, price: int, **extra: object):
    return client.post(
        f"/api/requests/{request_id}/offers",
        json={"supplier_id": "TX-JP-03", "vehicle_id": vehicle_id, "price_inr": price, **extra},
    )


def test_g1_one_supplier_assigns_two_cars_at_different_prices(client: TestClient) -> None:
    """G1: Edo can offer both of its cars, each with its own price."""
    request_id = _request(client)
    sedan = _offer(client, request_id, "EP-1", 12000)
    suv = _offer(client, request_id, "EP-2", 15000)
    assert sedan.status_code == 201, sedan.text
    assert suv.status_code == 201, suv.text
    assert sedan.json()["price_inr"] == 12000
    assert suv.json()["price_inr"] == 15000

    listed = client.get(f"/api/requests/{request_id}/offers").json()["offers"]
    assert {item["vehicle_id"] for item in listed} == {"EP-1", "EP-2"}


def test_g1_same_car_cannot_be_offered_twice(client: TestClient) -> None:
    """G1: a second offer of the same car on the same request is refused."""
    request_id = _request(client)
    assert _offer(client, request_id, "EP-1", 12000).status_code == 201
    again = _offer(client, request_id, "EP-1", 13000)
    assert again.status_code == 409
    assert again.json()["rule"] == "R7"


def test_g2_supplier_can_assign_the_chosen_type(client: TestClient) -> None:
    """G2: a sedan request accepts a sedan and refuses an SUV."""
    request_id = _request(client, car_type="SEDAN")
    suv = _offer(client, request_id, "EP-2", 13000)
    assert suv.status_code == 422
    assert suv.json()["rule"] == "R5"

    sedan = _offer(client, request_id, "EP-1", 12000)
    assert sedan.status_code == 201, sedan.text
    assert sedan.json()["vehicle_type"] == "SEDAN"


def test_g4_future_expiry_can_be_booked(client: TestClient) -> None:
    """G4: an offer that has not ended yet can be booked."""
    request_id = _request(client)
    created = _offer(client, request_id, "EP-1", 12000, expires_at="2099-04-10T18:00")
    assert created.status_code == 201, created.text
    assert created.json()["expires_at"] == "2099-04-10T18:00"

    booked = client.post(f"/api/offers/{created.json()['offer_id']}/book")
    assert booked.status_code == 201, booked.text


def test_g4_ended_offer_cannot_be_booked(client: TestClient) -> None:
    """G4: an offer whose end time has passed is refused at booking."""
    request_id = _request(client)
    created = _offer(client, request_id, "EP-1", 12000, expires_at="2020-01-01T00:00")
    assert created.status_code == 201, created.text

    booked = client.post(f"/api/offers/{created.json()['offer_id']}/book")
    assert booked.status_code == 409
    body = booked.json()
    assert body["rule"] == "G4"
    assert "cannot be booked" in body["message"]


def test_g4_bad_expiry_is_refused(client: TestClient) -> None:
    """G4: a nonsense expiry is refused when the car is assigned."""
    request_id = _request(client)
    response = _offer(client, request_id, "EP-1", 12000, expires_at="tomorrow")
    assert response.status_code == 422
    assert response.json()["rule"] == "G4"
