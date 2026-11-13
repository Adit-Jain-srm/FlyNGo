"""Integration tests for flight change requests (Milestone M7)."""

import pytest
from fastapi.testclient import TestClient


def _create_booking_helper(client: TestClient) -> dict:
    """Helper to post an offer and confirm booking on REQ-0001 (HND to Shibuya)."""
    res = client.post(
        "/api/requests/REQ-0001/offers",
        json={"supplier_id": "TX-JP-01", "vehicle_id": "SC-3", "price_inr": 4200},
    )
    assert res.status_code == 201
    offer_id = res.json()["offer_id"]

    book_res = client.post(f"/api/offers/{offer_id}/book")
    assert book_res.status_code == 201
    return book_res.json()


def test_change_request_r2_validation(client: TestClient):
    """Submitting a change with pickup earlier than landing + 60m fails Rule R2."""
    booking = _create_booking_helper(client)
    booking_no = booking["booking_number"]

    # FL-1131 lands at HND on 2027-04-08T06:50
    # Landing + 25m = 07:15 -> Violates R2
    bad_res = client.post(
        f"/api/bookings/{booking_no}/changes",
        json={
            "new_flight_id": "FL-1131",
            "new_pickup_local": "2027-04-08T07:15",
        },
    )
    assert bad_res.status_code == 422
    err = bad_res.json()
    assert err["rule"] == "R2"


def test_change_request_accept_flow(client: TestClient):
    """Happy path: traveler requests flight change, supplier accepts, booking is updated."""
    booking = _create_booking_helper(client)
    booking_no = booking["booking_number"]

    # FL-1131 lands at HND on 2027-04-08T06:50
    # Valid pickup: 08:30 (landing + 100m)
    change_res = client.post(
        f"/api/bookings/{booking_no}/changes",
        json={
            "new_flight_id": "FL-1131",
            "new_pickup_local": "2027-04-08T08:30",
        },
    )
    assert change_res.status_code == 201
    change = change_res.json()
    assert change["status"] == "WAITING"
    change_id = change["change_id"]

    # Attempting duplicate WAITING change -> 409
    dup_res = client.post(
        f"/api/bookings/{booking_no}/changes",
        json={
            "new_flight_id": "FL-1131",
            "new_pickup_local": "2027-04-08T08:30",
        },
    )
    assert dup_res.status_code == 409

    # Supplier accepts
    accept_res = client.post(f"/api/changes/{change_id}/accept")
    assert accept_res.status_code == 200
    accepted_change = accept_res.json()
    assert accepted_change["status"] == "ACCEPTED"

    # Verify booking updated
    b_updated = client.get(f"/api/bookings/{booking_no}").json()
    assert b_updated["flight_id"] == "FL-1131"
    assert b_updated["pickup_local"] == "2027-04-08T08:30"


def test_change_request_supplier_reject(client: TestClient):
    """Supplier rejects flight change: status becomes REJECTED, original booking unchanged."""
    booking = _create_booking_helper(client)
    booking_no = booking["booking_number"]
    orig_pickup = booking["pickup_local"]

    change_res = client.post(
        f"/api/bookings/{booking_no}/changes",
        json={
            "new_flight_id": "FL-1131",
            "new_pickup_local": "2027-04-08T08:30",
        },
    )
    assert change_res.status_code == 201
    change_id = change_res.json()["change_id"]

    # Reject
    rej_res = client.post(
        f"/api/changes/{change_id}/reject",
        json={"reason": "Driver not available at 08:30"},
    )
    assert rej_res.status_code == 200
    assert rej_res.json()["status"] == "REJECTED"

    # Booking remains unchanged
    b_check = client.get(f"/api/bookings/{booking_no}").json()
    assert b_check["pickup_local"] == orig_pickup
