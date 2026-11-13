"""Seed open requests from data/problem-2/open_requests.json."""

from pathlib import Path
import sqlite3

from backend.app.config import DATA_DIR
from backend.app.db.connection import get_connection
from backend.app.db.refdata_loader import _load_json, normalize_datetime


def seed_open_requests(
    conn: sqlite3.Connection | None = None,
    data_dir: Path | None = None,
) -> int:
    """Seed initial open requests (REQ-0001..0003) if not already present.

    Derives airport_code, city, area, and passengers from reference tables.
    Returns the count of seeded requests.
    """
    should_close = False
    if conn is None:
        conn = get_connection()
        should_close = True

    base_dir = data_dir or DATA_DIR
    open_req_file = base_dir / "problem-2" / "open_requests.json"

    if not open_req_file.exists():
        if should_close:
            conn.close()
        return 0

    requests_data = _load_json(open_req_file)
    seeded_count = 0

    try:
        cur = conn.cursor()
        cur.execute("BEGIN TRANSACTION;")

        for req in requests_data:
            req_id = req["request_id"]

            # Check if already seeded
            row = cur.execute(
                "SELECT request_id FROM ride_requests WHERE request_id = ?",
                (req_id,),
            ).fetchone()
            if row is not None:
                continue

            flight_id = req["flight_id"]
            hotel_id = req["hotel_id"]

            # Lookup flight's arrival airport
            flight = cur.execute(
                "SELECT to_airport FROM flights WHERE flight_id = ? AND is_active = 1",
                (flight_id,),
            ).fetchone()
            if not flight:
                continue
            airport_code = flight["to_airport"]

            # Lookup hotel's city and area
            hotel = cur.execute(
                "SELECT city, area FROM hotels WHERE hotel_id = ? AND is_active = 1",
                (hotel_id,),
            ).fetchone()
            if not hotel:
                continue
            city = hotel["city"]
            area = hotel["area"]

            adults = req["adults"]
            child_ages = req.get("child_ages", [])
            passengers = adults + len(child_ages)
            pickup_norm = normalize_datetime(req["pickup"])
            car_type = req.get("car_type")
            price_inr = req["price_inr"]

            cur.execute(
                """
                INSERT INTO ride_requests (
                    request_id, source, traveler_name, flight_id, hotel_id,
                    airport_code, city, area, adults, passengers,
                    large_bags, small_bags, pickup_local, car_type,
                    price_inr, status, is_active, updated_at
                )
                VALUES (?, 'SEED', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'OPEN', 1, CURRENT_TIMESTAMP)
                """,
                (
                    req_id,
                    req.get("traveler_name"),
                    flight_id,
                    hotel_id,
                    airport_code,
                    city,
                    area,
                    adults,
                    passengers,
                    req.get("large_bags", 0),
                    req.get("small_bags", 0),
                    pickup_norm,
                    car_type,
                    price_inr,
                ),
            )

            for idx, age in enumerate(child_ages, start=1):
                cur.execute(
                    """
                    INSERT INTO request_children (request_id, child_no, age, is_active, updated_at)
                    VALUES (?, ?, ?, 1, CURRENT_TIMESTAMP)
                    """,
                    (req_id, idx, age),
                )

            seeded_count += 1

        conn.commit()
        return seeded_count
    except Exception:
        conn.rollback()
        raise
    finally:
        if should_close:
            conn.close()
