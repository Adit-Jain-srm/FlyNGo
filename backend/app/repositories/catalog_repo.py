"""Catalog repository for airports, flights, hotels, routes, and vehicle capacities."""

import sqlite3
from typing import Any


def get_arrival_airports(conn: sqlite3.Connection) -> list[sqlite3.Row]:
    """Retrieve the 5 destination airports receiving ride offers (NRT, HND, KIX, DXB, AUH)."""
    query = """
        SELECT a.code, a.name, a.city, a.country, a.timezone
        FROM airports a
        WHERE a.is_active = 1
          AND a.code IN ('NRT', 'HND', 'KIX', 'DXB', 'AUH')
        ORDER BY a.country, a.city;
    """
    return conn.execute(query).fetchall()


def get_flights(conn: sqlite3.Connection, airport: str, date: str) -> list[sqlite3.Row]:
    """Retrieve arrival flights for a given airport and arrival date.

    Uses partial index: ix_flights_arrival(to_airport, arrival_date) WHERE is_active = 1.
    """
    query = """
        SELECT flight_id, airline, flight_number, from_airport, to_airport,
               departure_local, arrival_local, arrival_date, stops, duration_minutes, cabin
        FROM flights
        WHERE to_airport = ? AND arrival_date = ? AND is_active = 1
        ORDER BY arrival_local;
    """
    return conn.execute(query, (airport, date)).fetchall()


def get_flight_by_id(conn: sqlite3.Connection, flight_id: str) -> sqlite3.Row | None:
    """Retrieve a single active flight by ID."""
    query = "SELECT * FROM flights WHERE flight_id = ? AND is_active = 1;"
    return conn.execute(query, (flight_id,)).fetchone()


def get_airport_cities(conn: sqlite3.Connection, airport_code: str) -> list[str]:
    """Retrieve the list of cities served by an airport."""
    query = """
        SELECT city FROM airport_cities
        WHERE airport_code = ? AND is_active = 1
        ORDER BY city;
    """
    rows = conn.execute(query, (airport_code,)).fetchall()
    return [row["city"] for row in rows]


def get_hotels_by_airport(
    conn: sqlite3.Connection,
    airport_code: str,
    query_str: str | None = None,
) -> list[sqlite3.Row]:
    """Retrieve hotels located in cities served by the specified airport.

    Uses index ix_hotels_city_name with prefix filtering.
    """
    if query_str and query_str.strip():
        pattern = f"%{query_str.strip()}%"
        sql = """
            SELECT DISTINCT h.hotel_id, h.name, h.city, h.area, h.stars, h.rating
            FROM airport_cities ac
            JOIN hotels h ON h.city = ac.city AND h.is_active = 1
            WHERE ac.airport_code = ? AND ac.is_active = 1
              AND (h.name LIKE ? OR h.area LIKE ?)
            ORDER BY h.name;
        """
        return conn.execute(sql, (airport_code, pattern, pattern)).fetchall()
    else:
        sql = """
            SELECT DISTINCT h.hotel_id, h.name, h.city, h.area, h.stars, h.rating
            FROM airport_cities ac
            JOIN hotels h ON h.city = ac.city AND h.is_active = 1
            WHERE ac.airport_code = ? AND ac.is_active = 1
            ORDER BY h.name;
        """
        return conn.execute(sql, (airport_code,)).fetchall()


def get_hotel_by_id(conn: sqlite3.Connection, hotel_id: str) -> sqlite3.Row | None:
    """Retrieve a single active hotel by ID."""
    query = "SELECT * FROM hotels WHERE hotel_id = ? AND is_active = 1;"
    return conn.execute(query, (hotel_id,)).fetchone()


def get_route(
    conn: sqlite3.Connection,
    airport: str,
    city: str,
    area: str,
) -> sqlite3.Row | None:
    """Retrieve route details by primary key (airport, city, area)."""
    query = """
        SELECT airport, city, area, distance_km, drive_minutes, price_min_inr, price_max_inr
        FROM routes
        WHERE airport = ? AND city = ? AND area = ? AND is_active = 1;
    """
    return conn.execute(query, (airport, city, area)).fetchone()


def get_vehicle_type_limits(conn: sqlite3.Connection) -> list[sqlite3.Row]:
    """Retrieve maximum capacity and available count for each vehicle type."""
    query = """
        SELECT type,
               MAX(seats) AS max_seats,
               MAX(large_bags) AS max_large_bags,
               MAX(small_bags) AS max_small_bags,
               COUNT(*) AS available_fleet_count
        FROM vehicles
        WHERE is_active = 1
        GROUP BY type
        ORDER BY max_seats;
    """
    return conn.execute(query).fetchall()
