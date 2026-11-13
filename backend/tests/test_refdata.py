"""Unit and integration tests for reference data loader and §5 data facts."""

import re
import sqlite3
from fastapi.testclient import TestClient

from backend.app.db.refdata_loader import load_reference_data
from backend.app.db.seed import seed_open_requests


def test_section_5_verified_data_facts(temp_db: sqlite3.Connection) -> None:
    """Verify all Section 5 data facts documented in DESIGN.md."""
    cur = temp_db.cursor()

    # 1. Suppliers and cars
    row = cur.execute("SELECT COUNT(*) AS cnt FROM suppliers WHERE is_active = 1").fetchone()
    assert row["cnt"] == 11, f"Expected 11 suppliers, got {row['cnt']}"

    row = cur.execute("SELECT COUNT(*) AS cnt FROM vehicles WHERE is_active = 1").fetchone()
    assert row["cnt"] == 28, f"Expected 28 vehicles, got {row['cnt']}"

    v_types = dict(
        cur.execute(
            "SELECT type, COUNT(*) AS cnt FROM vehicles WHERE is_active = 1 GROUP BY type"
        ).fetchall()
    )
    assert v_types == {"SUV": 11, "SEDAN": 8, "BUS": 5, "HATCHBACK": 4}

    # Largest car has 9 seats, 6 large bags, 6 small bags
    largest = cur.execute(
        """
        SELECT MAX(seats) AS max_seats, MAX(large_bags) AS max_lb, MAX(small_bags) AS max_sb
        FROM vehicles WHERE is_active = 1
        """
    ).fetchone()
    assert largest["max_seats"] == 9
    assert largest["max_lb"] == 6
    assert largest["max_sb"] == 6

    # 2. Flights
    row = cur.execute("SELECT COUNT(*) AS cnt FROM flights WHERE is_active = 1").fetchone()
    assert row["cnt"] == 469, f"Expected 469 flights, got {row['cnt']}"

    # 240 land at NRT, HND, KIX, DXB or AUH between 1 and 20 April 2027
    target_airports = ("NRT", "HND", "KIX", "DXB", "AUH")
    row = cur.execute(
        """
        SELECT COUNT(*) AS cnt FROM flights
        WHERE is_active = 1
          AND to_airport IN (?, ?, ?, ?, ?)
          AND arrival_date BETWEEN '2027-04-01' AND '2027-04-20'
        """,
        target_airports,
    ).fetchone()
    assert row["cnt"] == 240, f"Expected 240 target landing flights, got {row['cnt']}"

    # 3. Hotels
    row = cur.execute("SELECT COUNT(*) AS cnt FROM hotels WHERE is_active = 1").fetchone()
    assert row["cnt"] == 49, f"Expected 49 hotels, got {row['cnt']}"

    hotel_counts_by_ap = dict(
        cur.execute(
            """
            SELECT ac.airport_code, COUNT(DISTINCT h.hotel_id) AS cnt
            FROM airport_cities ac
            JOIN hotels h ON h.city = ac.city AND h.is_active = 1
            WHERE ac.is_active = 1 AND ac.airport_code IN ('NRT', 'HND', 'KIX', 'DXB', 'AUH')
            GROUP BY ac.airport_code
            """
        ).fetchall()
    )
    assert hotel_counts_by_ap.get("NRT") == 13
    assert hotel_counts_by_ap.get("HND") == 13
    assert hotel_counts_by_ap.get("KIX") == 22
    assert hotel_counts_by_ap.get("DXB") == 14
    assert hotel_counts_by_ap.get("AUH") == 6

    # 4. Routes
    row = cur.execute("SELECT COUNT(*) AS cnt FROM routes WHERE is_active = 1").fetchone()
    assert row["cnt"] == 33, f"Expected 33 routes, got {row['cnt']}"

    route_stats = cur.execute(
        """
        SELECT
            MIN(price_min_inr) AS min_p,
            MAX(price_max_inr) AS max_p,
            MIN(drive_minutes) AS min_d,
            MAX(drive_minutes) AS max_d
        FROM routes WHERE is_active = 1
        """
    ).fetchone()
    assert route_stats["min_p"] == 700
    assert route_stats["max_p"] == 23900
    assert route_stats["min_d"] == 16
    assert route_stats["max_d"] == 134

    # 5. Open Requests seeded
    row = cur.execute("SELECT COUNT(*) AS cnt FROM ride_requests WHERE is_active = 1").fetchone()
    assert row["cnt"] == 3

    req_ids = [r["request_id"] for r in cur.execute("SELECT request_id FROM ride_requests WHERE is_active = 1 ORDER BY request_id").fetchall()]
    assert req_ids == ["REQ-0001", "REQ-0002", "REQ-0003"]


def test_idempotent_reload(temp_db: sqlite3.Connection) -> None:
    """Verify that calling the loader and seeder multiple times is idempotent."""
    cur = temp_db.cursor()
    initial_flights = cur.execute("SELECT COUNT(*) AS cnt FROM flights WHERE is_active = 1").fetchone()["cnt"]
    initial_suppliers = cur.execute("SELECT COUNT(*) AS cnt FROM suppliers WHERE is_active = 1").fetchone()["cnt"]
    initial_requests = cur.execute("SELECT COUNT(*) AS cnt FROM ride_requests WHERE is_active = 1").fetchone()["cnt"]

    # Re-run loader and seeder
    load_reference_data(temp_db)
    seed_open_requests(temp_db)

    after_flights = cur.execute("SELECT COUNT(*) AS cnt FROM flights WHERE is_active = 1").fetchone()["cnt"]
    after_suppliers = cur.execute("SELECT COUNT(*) AS cnt FROM suppliers WHERE is_active = 1").fetchone()["cnt"]
    after_requests = cur.execute("SELECT COUNT(*) AS cnt FROM ride_requests WHERE is_active = 1").fetchone()["cnt"]

    assert initial_flights == after_flights
    assert initial_suppliers == after_suppliers
    assert initial_requests == after_requests


def test_datetime_normalisation(temp_db: sqlite3.Connection) -> None:
    """Verify all timestamps conform strictly to YYYY-MM-DDTHH:MM (16 chars)."""
    iso_minute_pattern = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}$")
    cur = temp_db.cursor()

    for row in cur.execute("SELECT departure_local, arrival_local, arrival_date FROM flights WHERE is_active = 1").fetchall():
        assert iso_minute_pattern.match(row["departure_local"]), f"Bad format: {row['departure_local']}"
        assert iso_minute_pattern.match(row["arrival_local"]), f"Bad format: {row['arrival_local']}"
        assert len(row["arrival_date"]) == 10

    for row in cur.execute("SELECT start_local, end_local FROM booked_rides WHERE is_active = 1").fetchall():
        assert iso_minute_pattern.match(row["start_local"]), f"Bad format: {row['start_local']}"
        assert iso_minute_pattern.match(row["end_local"]), f"Bad format: {row['end_local']}"

    for row in cur.execute("SELECT pickup_local FROM ride_requests WHERE is_active = 1").fetchall():
        assert iso_minute_pattern.match(row["pickup_local"]), f"Bad format: {row['pickup_local']}"


def test_health_api(client: TestClient) -> None:
    """Verify GET /api/health returns healthy status and exact counts."""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    counts = data["counts"]
    assert counts["suppliers"] == 11
    assert counts["vehicles"] == 28
    assert counts["flights"] == 469
    assert counts["hotels"] == 49
    assert counts["routes"] == 33
    assert counts["booked_rides"] == 6
    assert counts["ride_requests"] == 3
