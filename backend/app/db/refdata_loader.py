"""Reference data loader: upserts JSON catalog and problem data into SQLite tables.

Implements startup upsert, soft-deactivation of missing keys, datetime
normalisation (YYYY-MM-DDTHH:MM), and one atomic transaction.
"""

import json
from pathlib import Path
import sqlite3
from typing import Any

from backend.app.config import DATA_DIR
from backend.app.db.connection import get_connection


def normalize_datetime(dt_str: str) -> str:
    """Normalise ISO datetime string to YYYY-MM-DDTHH:MM (16 characters).

    Example: '2027-04-01T07:20:00' -> '2027-04-01T07:20'
    """
    if not dt_str:
        return dt_str
    clean = dt_str.strip()
    if len(clean) >= 16 and clean[10] == "T":
        return clean[:16]
    return clean


def _load_json(file_path: Path) -> Any:
    """Load and parse a JSON file."""
    if not file_path.exists():
        raise FileNotFoundError(f"Reference data file not found: {file_path}")
    with open(file_path, encoding="utf-8") as f:
        return json.load(f)


def load_reference_data(
    conn: sqlite3.Connection | None = None,
    data_dir: Path | None = None,
) -> dict[str, int]:
    """Load and upsert all reference data from JSON files into SQLite.

    Returns a dictionary of loaded table row counts.
    """
    should_close = False
    if conn is None:
        conn = get_connection()
        should_close = True

    base_dir = data_dir or DATA_DIR
    catalog_dir = base_dir / "catalog"
    problem_dir = base_dir / "problem-2"

    counts: dict[str, int] = {}

    try:
        cur = conn.cursor()
        cur.execute("BEGIN TRANSACTION;")

        # -------------------------------------------------------------
        # 1. Airports & Airport Cities
        # -------------------------------------------------------------
        airports_data = _load_json(catalog_dir / "airports.json")
        active_airports = set()
        active_airport_cities = set()

        for ap in airports_data:
            code = ap["code"]
            active_airports.add(code)
            cur.execute(
                """
                INSERT INTO airports (code, name, city, country, timezone, is_active, updated_at)
                VALUES (?, ?, ?, ?, ?, 1, CURRENT_TIMESTAMP)
                ON CONFLICT(code) DO UPDATE SET
                    name = excluded.name,
                    city = excluded.city,
                    country = excluded.country,
                    timezone = excluded.timezone,
                    is_active = 1,
                    updated_at = CURRENT_TIMESTAMP;
                """,
                (code, ap["name"], ap["city"], ap["country"], ap["timezone"]),
            )

            for city in ap.get("serves_cities", []):
                active_airport_cities.add((code, city))
                cur.execute(
                    """
                    INSERT INTO airport_cities (airport_code, city, is_active, updated_at)
                    VALUES (?, ?, 1, CURRENT_TIMESTAMP)
                    ON CONFLICT(airport_code, city) DO UPDATE SET
                        is_active = 1,
                        updated_at = CURRENT_TIMESTAMP;
                    """,
                    (code, city),
                )

        # Soft-deactivate missing airports & airport_cities
        for row in cur.execute("SELECT code FROM airports WHERE is_active = 1").fetchall():
            if row["code"] not in active_airports:
                cur.execute(
                    "UPDATE airports SET is_active = 0, updated_at = CURRENT_TIMESTAMP WHERE code = ?",
                    (row["code"],),
                )

        for row in cur.execute("SELECT airport_code, city FROM airport_cities WHERE is_active = 1").fetchall():
            if (row["airport_code"], row["city"]) not in active_airport_cities:
                cur.execute(
                    "UPDATE airport_cities SET is_active = 0, updated_at = CURRENT_TIMESTAMP WHERE airport_code = ? AND city = ?",
                    (row["airport_code"], row["city"]),
                )

        counts["airports"] = len(active_airports)
        counts["airport_cities"] = len(active_airport_cities)

        # -------------------------------------------------------------
        # 2. Flights
        # -------------------------------------------------------------
        flights_data = _load_json(catalog_dir / "flights.json")
        active_flights = set()

        for fl in flights_data:
            flight_id = fl["flight_id"]
            active_flights.add(flight_id)
            dep_norm = normalize_datetime(fl["departure_local"])
            arr_norm = normalize_datetime(fl["arrival_local"])
            arrival_date = arr_norm[:10]

            cur.execute(
                """
                INSERT INTO flights (
                    flight_id, airline, flight_number, from_airport, to_airport,
                    departure_local, arrival_local, arrival_date, stops,
                    duration_minutes, cabin, is_active, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, CURRENT_TIMESTAMP)
                ON CONFLICT(flight_id) DO UPDATE SET
                    airline = excluded.airline,
                    flight_number = excluded.flight_number,
                    from_airport = excluded.from_airport,
                    to_airport = excluded.to_airport,
                    departure_local = excluded.departure_local,
                    arrival_local = excluded.arrival_local,
                    arrival_date = excluded.arrival_date,
                    stops = excluded.stops,
                    duration_minutes = excluded.duration_minutes,
                    cabin = excluded.cabin,
                    is_active = 1,
                    updated_at = CURRENT_TIMESTAMP;
                """,
                (
                    flight_id,
                    fl["airline"],
                    fl["flight_number"],
                    fl["from"],
                    fl["to"],
                    dep_norm,
                    arr_norm,
                    arrival_date,
                    fl.get("stops", 0),
                    fl.get("duration_minutes", 0),
                    fl.get("cabin"),
                ),
            )

        for row in cur.execute("SELECT flight_id FROM flights WHERE is_active = 1").fetchall():
            if row["flight_id"] not in active_flights:
                cur.execute(
                    "UPDATE flights SET is_active = 0, updated_at = CURRENT_TIMESTAMP WHERE flight_id = ?",
                    (row["flight_id"],),
                )

        counts["flights"] = len(active_flights)

        # -------------------------------------------------------------
        # 3. Hotels
        # -------------------------------------------------------------
        hotels_data = _load_json(catalog_dir / "hotels.json")
        active_hotels = set()

        for htl in hotels_data:
            hotel_id = htl["hotel_id"]
            active_hotels.add(hotel_id)
            cur.execute(
                """
                INSERT INTO hotels (hotel_id, name, city, area, stars, rating, is_active, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, 1, CURRENT_TIMESTAMP)
                ON CONFLICT(hotel_id) DO UPDATE SET
                    name = excluded.name,
                    city = excluded.city,
                    area = excluded.area,
                    stars = excluded.stars,
                    rating = excluded.rating,
                    is_active = 1,
                    updated_at = CURRENT_TIMESTAMP;
                """,
                (hotel_id, htl["name"], htl["city"], htl["area"], htl.get("stars"), htl.get("rating")),
            )

        for row in cur.execute("SELECT hotel_id FROM hotels WHERE is_active = 1").fetchall():
            if row["hotel_id"] not in active_hotels:
                cur.execute(
                    "UPDATE hotels SET is_active = 0, updated_at = CURRENT_TIMESTAMP WHERE hotel_id = ?",
                    (row["hotel_id"],),
                )

        counts["hotels"] = len(active_hotels)

        # -------------------------------------------------------------
        # 4. Routes
        # -------------------------------------------------------------
        routes_data = _load_json(problem_dir / "routes.json")
        active_routes = set()

        for rt in routes_data:
            key = (rt["airport"], rt["city"], rt["area"])
            active_routes.add(key)
            cur.execute(
                """
                INSERT INTO routes (
                    airport, city, area, distance_km, drive_minutes,
                    price_min_inr, price_max_inr, is_active, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, 1, CURRENT_TIMESTAMP)
                ON CONFLICT(airport, city, area) DO UPDATE SET
                    distance_km = excluded.distance_km,
                    drive_minutes = excluded.drive_minutes,
                    price_min_inr = excluded.price_min_inr,
                    price_max_inr = excluded.price_max_inr,
                    is_active = 1,
                    updated_at = CURRENT_TIMESTAMP;
                """,
                (
                    rt["airport"],
                    rt["city"],
                    rt["area"],
                    rt["distance_km"],
                    rt["drive_minutes"],
                    rt["price_min_inr"],
                    rt["price_max_inr"],
                ),
            )

        for row in cur.execute("SELECT airport, city, area FROM routes WHERE is_active = 1").fetchall():
            if (row["airport"], row["city"], row["area"]) not in active_routes:
                cur.execute(
                    "UPDATE routes SET is_active = 0, updated_at = CURRENT_TIMESTAMP WHERE airport = ? AND city = ? AND area = ?",
                    (row["airport"], row["city"], row["area"]),
                )

        counts["routes"] = len(active_routes)

        # -------------------------------------------------------------
        # 5. Taxi Companies (Suppliers, Airports, Areas, Vehicles)
        # -------------------------------------------------------------
        companies_data = _load_json(problem_dir / "taxi_companies.json")
        active_suppliers = set()
        active_supplier_airports = set()
        active_supplier_areas = set()
        active_vehicles = set()

        for comp in companies_data:
            sid = comp["company_id"]
            active_suppliers.add(sid)
            cur.execute(
                """
                INSERT INTO suppliers (supplier_id, name, service_from, service_until, rating, is_active, updated_at)
                VALUES (?, ?, ?, ?, ?, 1, CURRENT_TIMESTAMP)
                ON CONFLICT(supplier_id) DO UPDATE SET
                    name = excluded.name,
                    service_from = excluded.service_from,
                    service_until = excluded.service_until,
                    rating = excluded.rating,
                    is_active = 1,
                    updated_at = CURRENT_TIMESTAMP;
                """,
                (sid, comp["name"], comp["service_from"], comp["service_until"], comp.get("rating")),
            )

            for ap_code in comp.get("airports", []):
                active_supplier_airports.add((ap_code, sid))
                cur.execute(
                    """
                    INSERT INTO supplier_airports (airport_code, supplier_id, is_active, updated_at)
                    VALUES (?, ?, 1, CURRENT_TIMESTAMP)
                    ON CONFLICT(airport_code, supplier_id) DO UPDATE SET
                        is_active = 1,
                        updated_at = CURRENT_TIMESTAMP;
                    """,
                    (ap_code, sid),
                )

            for area_item in comp.get("areas", []):
                key = (area_item["city"], area_item["area"], sid)
                active_supplier_areas.add(key)
                cur.execute(
                    """
                    INSERT INTO supplier_areas (city, area, supplier_id, is_active, updated_at)
                    VALUES (?, ?, ?, 1, CURRENT_TIMESTAMP)
                    ON CONFLICT(city, area, supplier_id) DO UPDATE SET
                        is_active = 1,
                        updated_at = CURRENT_TIMESTAMP;
                    """,
                    (area_item["city"], area_item["area"], sid),
                )

            for veh in comp.get("vehicles", []):
                vid = veh["vehicle_id"]
                active_vehicles.add(vid)
                cur.execute(
                    """
                    INSERT INTO vehicles (vehicle_id, supplier_id, type, seats, large_bags, small_bags, is_active, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, 1, CURRENT_TIMESTAMP)
                    ON CONFLICT(vehicle_id) DO UPDATE SET
                        supplier_id = excluded.supplier_id,
                        type = excluded.type,
                        seats = excluded.seats,
                        large_bags = excluded.large_bags,
                        small_bags = excluded.small_bags,
                        is_active = 1,
                        updated_at = CURRENT_TIMESTAMP;
                    """,
                    (vid, sid, veh["type"], veh["seats"], veh["large_bags"], veh["small_bags"]),
                )

        # Soft-deactivate missing suppliers, supplier_airports, supplier_areas, vehicles
        for row in cur.execute("SELECT supplier_id FROM suppliers WHERE is_active = 1").fetchall():
            if row["supplier_id"] not in active_suppliers:
                cur.execute(
                    "UPDATE suppliers SET is_active = 0, updated_at = CURRENT_TIMESTAMP WHERE supplier_id = ?",
                    (row["supplier_id"],),
                )

        for row in cur.execute("SELECT airport_code, supplier_id FROM supplier_airports WHERE is_active = 1").fetchall():
            if (row["airport_code"], row["supplier_id"]) not in active_supplier_airports:
                cur.execute(
                    "UPDATE supplier_airports SET is_active = 0, updated_at = CURRENT_TIMESTAMP WHERE airport_code = ? AND supplier_id = ?",
                    (row["airport_code"], row["supplier_id"]),
                )

        for row in cur.execute("SELECT city, area, supplier_id FROM supplier_areas WHERE is_active = 1").fetchall():
            if (row["city"], row["area"], row["supplier_id"]) not in active_supplier_areas:
                cur.execute(
                    "UPDATE supplier_areas SET is_active = 0, updated_at = CURRENT_TIMESTAMP WHERE city = ? AND area = ? AND supplier_id = ?",
                    (row["city"], row["area"], row["supplier_id"]),
                )

        for row in cur.execute("SELECT vehicle_id FROM vehicles WHERE is_active = 1").fetchall():
            if row["vehicle_id"] not in active_vehicles:
                cur.execute(
                    "UPDATE vehicles SET is_active = 0, updated_at = CURRENT_TIMESTAMP WHERE vehicle_id = ?",
                    (row["vehicle_id"],),
                )

        counts["suppliers"] = len(active_suppliers)
        counts["supplier_airports"] = len(active_supplier_airports)
        counts["supplier_areas"] = len(active_supplier_areas)
        counts["vehicles"] = len(active_vehicles)

        # -------------------------------------------------------------
        # 6. Booked Rides
        # -------------------------------------------------------------
        booked_data = _load_json(problem_dir / "booked_rides.json")
        active_booked = set()

        for ride in booked_data:
            rid = ride["ride_id"]
            active_booked.add(rid)
            start_norm = normalize_datetime(ride["start"])
            end_norm = normalize_datetime(ride["end"])
            cur.execute(
                """
                INSERT INTO booked_rides (ride_id, supplier_id, vehicle_id, start_local, end_local, is_active, updated_at)
                VALUES (?, ?, ?, ?, ?, 1, CURRENT_TIMESTAMP)
                ON CONFLICT(ride_id) DO UPDATE SET
                    supplier_id = excluded.supplier_id,
                    vehicle_id = excluded.vehicle_id,
                    start_local = excluded.start_local,
                    end_local = excluded.end_local,
                    is_active = 1,
                    updated_at = CURRENT_TIMESTAMP;
                """,
                (rid, ride["company_id"], ride["vehicle_id"], start_norm, end_norm),
            )

        for row in cur.execute("SELECT ride_id FROM booked_rides WHERE is_active = 1").fetchall():
            if row["ride_id"] not in active_booked:
                cur.execute(
                    "UPDATE booked_rides SET is_active = 0, updated_at = CURRENT_TIMESTAMP WHERE ride_id = ?",
                    (row["ride_id"],),
                )

        counts["booked_rides"] = len(active_booked)

        conn.commit()
        return counts
    except Exception:
        conn.rollback()
        raise
    finally:
        if should_close:
            conn.close()
