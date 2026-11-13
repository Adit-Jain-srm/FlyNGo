"""Integration tests for supplier vehicle assignment, offer creation, and offer rejection."""

import pytest
from fastapi.testclient import TestClient


def test_offer_assignment_rules(client: TestClient) -> None:
    """Test assigning cars to a request with R4-R7 rule enforcement."""
    # 1. Post request for Menon scenario
    req_res = client.post(
        "/api/requests",
        json={
            "traveler_name": "Menon Family",
            "flight_id": "FL-401",
            "hotel_id": "HTL-TYO-004",
            "adults": 2,
            "child_ages": [6],
            "large_bags": 3,
            "small_bags": 2,
            "pickup_local": "2027-04-10T11:30",
            "price_inr": 12000,
        },
    )
    assert req_res.status_code == 201
    req_id = req_res.json()["request_id"]

    # 2. Refuse assigning SC-2 (Busy because of RIDE-0001, Rule R6)
    offer_busy = client.post(
        f"/api/requests/{req_id}/offers",
        json={"supplier_id": "TX-JP-01", "vehicle_id": "SC-2", "price_inr": 12000},
    )
    assert offer_busy.status_code == 422
    err = offer_busy.json()
    assert err["rule"] == "R6"
    assert err["field"] == "vehicle_id"
    assert "busy until 14:00" in err["message"]

    # 3. Refuse assigning SC-3 with price below route minimum (Rule R3/R7)
    offer_bad_price = client.post(
        f"/api/requests/{req_id}/offers",
        json={"supplier_id": "TX-JP-01", "vehicle_id": "SC-3", "price_inr": 9000},
    )
    assert offer_bad_price.status_code == 422
    err = offer_bad_price.json()
    assert err["rule"] == "R3"
    assert err["allowed"] == {"min": 10200, "max": 16800}

    # 4. Successfully assign SC-3 (Sakura Cabs) at ₹12,000
    offer_ok = client.post(
        f"/api/requests/{req_id}/offers",
        json={"supplier_id": "TX-JP-01", "vehicle_id": "SC-3", "price_inr": 12000},
    )
    assert offer_ok.status_code == 201
    created_offer = offer_ok.json()
    assert created_offer["supplier_id"] == "TX-JP-01"
    assert created_offer["vehicle_id"] == "SC-3"
    assert created_offer["price_inr"] == 12000
    assert created_offer["status"] == "OPEN"
    sakura_offer_id = created_offer["offer_id"]

    # 5. Duplicate car assignment refused (one car offer per request)
    offer_dup = client.post(
        f"/api/requests/{req_id}/offers",
        json={"supplier_id": "TX-JP-01", "vehicle_id": "SC-3", "price_inr": 12000},
    )
    assert offer_dup.status_code == 409
    assert offer_dup.json()["rule"] == "R7"

    # 6. Second supplier: Edo Prime (TX-JP-03) assigns EP-2 at ₹13,000
    offer_edo = client.post(
        f"/api/requests/{req_id}/offers",
        json={"supplier_id": "TX-JP-03", "vehicle_id": "EP-2", "price_inr": 13000},
    )
    assert offer_edo.status_code == 201

    # 7. Query active offers for the request
    offers_res = client.get(f"/api/requests/{req_id}/offers")
    assert offers_res.status_code == 200
    offers_data = offers_res.json()
    assert len(offers_data["offers"]) == 2
    # Sorted by price ascending
    assert offers_data["offers"][0]["vehicle_id"] == "SC-3"
    assert offers_data["offers"][1]["vehicle_id"] == "EP-2"

    # 8. Traveler rejects Sakura offer
    reject_res = client.post(f"/api/offers/{sakura_offer_id}/reject")
    assert reject_res.status_code == 200
    assert reject_res.json()["status"] == "REJECTED"

    # 9. Verify offer is now rejected
    after_reject = client.get(f"/api/requests/{req_id}/offers").json()["offers"]
    # Rejected offer status is REJECTED
    sakura_offer = next(o for o in after_reject if o["offer_id"] == sakura_offer_id)
    assert sakura_offer["status"] == "REJECTED"
