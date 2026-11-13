"""Pure business rules validation functions (R1 - R9).

Keeps domain rules independent of database and HTTP transport layers.
"""

from datetime import datetime, timedelta
from typing import Any

from backend.app.errors import ConflictException, RuleViolationException


# -------------------------------------------------------------
# R1: Ride Request Requirements
# -------------------------------------------------------------
def validate_r1_request(
    arrival_airport: str,
    serves_cities: list[str],
    hotel_city: str,
    adults: int,
    child_ages: list[int],
    large_bags: int = 0,
    small_bags: int = 0,
) -> None:
    """Validate Rule R1: Arrival airport serves hotel city, adults >= 1, child ages 0-17."""
    if hotel_city not in serves_cities:
        raise RuleViolationException(
            rule="R1",
            field="hotel_id",
            message=f"Arrival airport {arrival_airport} does not serve {hotel_city}. Available cities: {', '.join(serves_cities)}.",
            allowed=serves_cities,
        )

    if adults < 1:
        raise RuleViolationException(
            rule="R1",
            field="adults",
            message="At least 1 adult passenger is required.",
            allowed={"min": 1},
        )

    for age in child_ages:
        if not (0 <= age <= 17):
            raise RuleViolationException(
                rule="R1",
                field="child_ages",
                message=f"Child age {age} is invalid. Child ages must be between 0 and 17.",
                allowed={"min": 0, "max": 17},
            )

    if large_bags < 0:
        raise RuleViolationException(
            rule="R1",
            field="large_bags",
            message="Large bags count cannot be negative.",
            allowed={"min": 0},
        )

    if small_bags < 0:
        raise RuleViolationException(
            rule="R1",
            field="small_bags",
            message="Small bags count cannot be negative.",
            allowed={"min": 0},
        )


# -------------------------------------------------------------
# R2: Pickup Window (Landing + 60 min to Landing + 24 hours)
# -------------------------------------------------------------
def compute_pickup_window(arrival_local: str) -> tuple[str, str, str]:
    """Compute (default, earliest, latest) pickup times for an arrival flight."""
    arrival_dt = datetime.fromisoformat(arrival_local)
    default_dt = arrival_dt + timedelta(minutes=60)
    earliest_dt = default_dt
    latest_dt = arrival_dt + timedelta(hours=24)

    return (
        default_dt.strftime("%Y-%m-%dT%H:%M"),
        earliest_dt.strftime("%Y-%m-%dT%H:%M"),
        latest_dt.strftime("%Y-%m-%dT%H:%M"),
    )


def validate_r2_pickup(pickup_local: str, arrival_local: str) -> None:
    """Validate Rule R2: Pickup must be at least landing + 60 min and within 24h."""
    default_p, earliest_p, latest_p = compute_pickup_window(arrival_local)

    if pickup_local < earliest_p or pickup_local > latest_p:
        raise RuleViolationException(
            rule="R2",
            field="pickup_local",
            message=f"Pickup time must be between {earliest_p} and {latest_p} (at least 60 minutes after landing and within 24 hours).",
            allowed={"min": earliest_p, "max": latest_p, "default": default_p},
        )


# -------------------------------------------------------------
# R3: Route Price Range
# -------------------------------------------------------------
def validate_r3_price(price_inr: int, price_min_inr: int, price_max_inr: int) -> None:
    """Validate Rule R3: Traveler price must fall within route min and max bounds."""
    if price_inr < price_min_inr or price_inr > price_max_inr:
        raise RuleViolationException(
            rule="R3",
            field="price_inr",
            message=f"Price ₹{price_inr:,} is outside the suggested route range (₹{price_min_inr:,} – ₹{price_max_inr:,}).",
            allowed={"min": price_min_inr, "max": price_max_inr},
        )


# -------------------------------------------------------------
# R4: Supplier Operational Eligibility
# -------------------------------------------------------------
def is_supplier_open_at_time(service_from: str, service_until: str, pickup_local: str) -> bool:
    """Check if pickup time falls within supplier opening hours (including overnight windows)."""
    pickup_time_str = pickup_local[11:16]
    if service_from <= service_until:
        return service_from <= pickup_time_str <= service_until
    else:
        # Crosses midnight (e.g. 05:00 to 01:00)
        return pickup_time_str >= service_from or pickup_time_str <= service_until


# -------------------------------------------------------------
# R6: Busy Interval Calculation
# -------------------------------------------------------------
def compute_ride_busy_interval(pickup_local: str, drive_minutes: int) -> tuple[str, str]:
    """Calculate busy interval [start, end) where end = pickup + 2 * drive_minutes."""
    start_dt = datetime.fromisoformat(pickup_local)
    end_dt = start_dt + timedelta(minutes=2 * drive_minutes)
    return (
        start_dt.strftime("%Y-%m-%dT%H:%M"),
        end_dt.strftime("%Y-%m-%dT%H:%M"),
    )
