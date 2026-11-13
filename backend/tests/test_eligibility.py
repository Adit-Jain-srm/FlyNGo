"""Eligibility and supplier dashboard tests (Menon scenario, overnight window, and B.3 funnel)."""

import sqlite3
from fastapi.testclient import TestClient

from backend.app.repositories import eligibility_repo, supplier_repo
from backend.app.services.offer_service import (
    get_car_advisories_for_request,
    get_requests_for_supplier,
    get_request_offers_and_status,
)


def test_menon_sakura_cabs_car_eligibility(client: TestClient, temp_db: sqlite3.Connection) -> None:
    """Menon scenario: Sakura Cabs (TX-JP-01) sees REQ-0004; SC-3 is free, SC-2 is busy (R6)."""
    # 1. Post Menon request
    res = client.post(
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
    assert res.status_code == 201
    req = res.json()
    req_id = req["request_id"]

    # 2. Sakura Cabs sees this request in dashboard (B.2 query)
    sakura_reqs = client.get("/api/suppliers/TX-JP-01/requests").json()
    req_ids = [r["request_id"] for r in sakura_reqs]
    assert req_id in req_ids

    # 3. Advisory badges for Sakura Cabs cars
    cars_res = client.get(f"/api/suppliers/TX-JP-01/requests/{req_id}/cars")
    assert cars_res.status_code == 200
    cars = {c["vehicle_id"]: c for c in cars_res.json()}

    # SC-1 (Sedan, 4 seats, 2 large bags) -> TOO_SMALL
    assert cars["SC-1"]["badge"] == "TOO_SMALL"
    assert "2 large bags < 3 required" in cars["SC-1"]["reason"]

    # SC-2 (SUV, 6 seats, 4 large bags) -> BUSY due to RIDE-0001 (11:00-14:00)
    assert cars["SC-2"]["badge"] == "BUSY"
    assert "Busy until 14:00" in cars["SC-2"]["reason"]

    # SC-3 (SUV, 6 seats, 4 large bags) -> FITS_FREE
    assert cars["SC-3"]["badge"] == "FITS_FREE"
    assert cars["SC-3"]["reason"] == "Fits and free"

    # SC-4 (Hatchback, 4 seats, 1 large bag) -> TOO_SMALL
    assert cars["SC-4"]["badge"] == "TOO_SMALL"


def test_menon_edo_prime_cars(client: TestClient) -> None:
    """Menon scenario: Edo Prime (TX-JP-03) has EP-1 and EP-2 free."""
    # REQ-0004 was created in Menon test or create fresh one
    res = client.post(
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
    req_id = res.json()["request_id"]

    cars_res = client.get(f"/api/suppliers/TX-JP-03/requests/{req_id}/cars")
    cars = {c["vehicle_id"]: c for c in cars_res.json()}

    assert cars["EP-1"]["badge"] == "FITS_FREE"
    assert cars["EP-2"]["badge"] == "FITS_FREE"


def test_marina_cabs_overnight_service_window(temp_db: sqlite3.Connection) -> None:
    """Marina Rides (TX-AE-05) operates 05:00 to 01:00 (crosses midnight) and is open at 00:30."""
    from backend.app.services.rules import is_supplier_open_at_time

    supplier = supplier_repo.get_supplier_by_id(temp_db, "TX-AE-05")
    assert supplier["service_from"] == "05:00"
    assert supplier["service_until"] == "01:00"

    assert is_supplier_open_at_time("05:00", "01:00", "2027-04-10T00:30") is True
    assert is_supplier_open_at_time("05:00", "01:00", "2027-04-10T03:00") is False  # closed at 3am


def test_req0002_no_supplier_funnel(client: TestClient) -> None:
    """REQ-0002 (KIX to Namba, SEDAN) has no eligible supplier; B.3 funnel reports why."""
    res = client.get("/api/requests/REQ-0002/offers")
    assert res.status_code == 200
    data = res.json()
    funnel = data["funnel"]

    assert funnel["has_eligible_supplier"] is False
    assert funnel["failing_step"] == "has_fitting_car"
    assert "No supplier has a vehicle with enough seats/luggage capacity" in funnel["plain_reason"]


def test_explain_query_plan_uses_indexes(temp_db: sqlite3.Connection) -> None:
    """EXPLAIN QUERY PLAN confirms B.1 query utilizes indexes rather than full table scans."""
    plan = temp_db.execute(
        """
        EXPLAIN QUERY PLAN
        SELECT s.supplier_id, v.vehicle_id
        FROM suppliers s
        JOIN supplier_airports sa ON sa.supplier_id = s.supplier_id AND sa.airport_code = 'NRT' AND sa.is_active = 1
        JOIN supplier_areas sr ON sr.supplier_id = s.supplier_id AND sr.city = 'Tokyo' AND sr.area = 'Ueno' AND sr.is_active = 1
        JOIN vehicles v ON v.supplier_id = s.supplier_id AND v.is_active = 1
          AND v.seats >= 3 AND v.large_bags >= 3 AND v.small_bags >= 2
        WHERE s.is_active = 1
          AND NOT EXISTS (SELECT 1 FROM bookings b WHERE b.vehicle_id = v.vehicle_id AND b.is_active = 1
                          AND b.busy_start < '2027-04-10T14:30' AND '2027-04-10T11:30' < b.busy_end)
          AND NOT EXISTS (SELECT 1 FROM booked_rides x WHERE x.vehicle_id = v.vehicle_id AND x.is_active = 1
                          AND x.start_local < '2027-04-10T14:30' AND '2027-04-10T11:30' < x.end_local);
        """
    ).fetchall()

    plan_details = " ".join([row["detail"] for row in plan])
    # Verifies indexes are referenced
    assert "USING" in plan_details or "INDEX" in plan_details
