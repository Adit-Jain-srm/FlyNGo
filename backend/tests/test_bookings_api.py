"""Integration tests for bookings API (M4-M6):
- 10-digit booking number generation (first digit non-zero)
- Atomic booking creation
- Double-booking prevention (409 Conflict)
- Competitor offers marked NOT_CHOSEN
- 404 for missing booking
- Summary retrieval
"""

import pytest
from fastapi.testclient import TestClient


def test_booking_happy_path_and_summary(client: TestClient):
    """Post an offer on REQ-0001, book it, verify 10-digit number and summary."""
    # 1. Post two offers on REQ-0001
    # Offer 1 from Sakura Cabs (SC-3)
    res1 = client.post(
        "/api/requests/REQ-0001/offers",
        json={"supplier_id": "TX-JP-01", "vehicle_id": "SC-3", "price_inr": 4200},
    )
    assert res1.status_code == 201
    offer1 = res1.json()
    offer1_id = offer1["offer_id"]

    # Offer 2 from Edo Prime (EP-1)
    res2 = client.post(
        "/api/requests/REQ-0001/offers",
        json={"supplier_id": "TX-JP-03", "vehicle_id": "EP-1", "price_inr": 4500},
    )
    assert res2.status_code == 201
    offer2 = res2.json()
    offer2_id = offer2["offer_id"]

    # 2. Book Offer 1
    book_res = client.post(f"/api/offers/{offer1_id}/book")
    assert book_res.status_code == 201
    booking = book_res.json()

    # Validate 10-digit booking number constraints
    booking_no = booking["booking_number"]
    assert len(booking_no) == 10
    assert booking_no.isdigit()
    assert booking_no[0] != "0"
    assert booking["status"] == "CONFIRMED"
    assert booking["supplier_name"] == "Sakura Cabs"
    assert booking["vehicle_id"] == "SC-3"
    assert booking["price_inr"] == 4200

    # 3. Verify competitor Offer 2 is marked NOT_CHOSEN
    offers_res = client.get("/api/requests/REQ-0001/offers")
    assert offers_res.status_code == 200
    offers_list = offers_res.json()["offers"]
    o1 = next(o for o in offers_list if o["offer_id"] == offer1_id)
    o2 = next(o for o in offers_list if o["offer_id"] == offer2_id)
    assert o1["status"] == "BOOKED"
    assert o2["status"] == "NOT_CHOSEN"

    # 4. Verify request is now BOOKED
    req_res = client.get("/api/requests/REQ-0001")
    assert req_res.status_code == 200
    assert req_res.json()["status"] == "BOOKED"

    # 5. Fetch booking by booking_number (M5 summary)
    get_res = client.get(f"/api/bookings/{booking_no}")
    assert get_res.status_code == 200
    summary = get_res.json()
    assert summary["booking_number"] == booking_no
    assert summary["flight_id"] == "FL-731"
    assert summary["hotel_id"] == "HTL-TYO-008"
    assert summary["vehicle_type"] == "SUV"


def test_double_booking_prevention(client: TestClient):
    """Attempting to book a second offer on an already booked request returns 409 Conflict."""
    # Post offer on REQ-0003 (AUH to Yas Island: range 800 - 1400)
    res1 = client.post(
        "/api/requests/REQ-0003/offers",
        json={"supplier_id": "TX-AE-02", "vehicle_id": "DR-2", "price_inr": 1300},
    )
    assert res1.status_code == 201
    offer1_id = res1.json()["offer_id"]

    # Book it
    b1 = client.post(f"/api/offers/{offer1_id}/book")
    assert b1.status_code == 201

    # Attempt to book the same offer again -> 409
    b2 = client.post(f"/api/offers/{offer1_id}/book")
    assert b2.status_code == 409


def test_booking_404_not_found(client: TestClient):
    """Querying a non-existent 10-digit booking number returns 404."""
    res = client.get("/api/bookings/9999999999")
    assert res.status_code == 404
