"""Unit tests for pure business rules R1, R2, and R3."""

import pytest
from backend.app.errors import RuleViolationException
from backend.app.services.rules import (
    compute_pickup_window,
    compute_ride_busy_interval,
    validate_r1_request,
    validate_r2_pickup,
    validate_r3_price,
)


def test_r1_valid_request() -> None:
    """R1: Valid parameters pass without exception."""
    validate_r1_request(
        arrival_airport="NRT",
        serves_cities=["Tokyo"],
        hotel_city="Tokyo",
        adults=2,
        child_ages=[6],
        large_bags=3,
        small_bags=2,
    )


def test_r1_city_not_served() -> None:
    """R1: Arrival airport not serving hotel city raises R1 violation."""
    with pytest.raises(RuleViolationException) as exc_info:
        validate_r1_request(
            arrival_airport="NRT",
            serves_cities=["Tokyo"],
            hotel_city="Osaka",
            adults=2,
            child_ages=[],
        )
    err = exc_info.value
    assert err.rule == "R1"
    assert err.field == "hotel_id"
    assert "does not serve Osaka" in err.message


def test_r1_zero_adults() -> None:
    """R1: Fewer than 1 adult raises R1 violation."""
    with pytest.raises(RuleViolationException) as exc_info:
        validate_r1_request(
            arrival_airport="NRT",
            serves_cities=["Tokyo"],
            hotel_city="Tokyo",
            adults=0,
            child_ages=[10],
        )
    err = exc_info.value
    assert err.rule == "R1"
    assert err.field == "adults"


def test_r1_invalid_child_age() -> None:
    """R1: Child age >= 18 raises R1 violation."""
    with pytest.raises(RuleViolationException) as exc_info:
        validate_r1_request(
            arrival_airport="NRT",
            serves_cities=["Tokyo"],
            hotel_city="Tokyo",
            adults=1,
            child_ages=[18],
        )
    err = exc_info.value
    assert err.rule == "R1"
    assert err.field == "child_ages"


def test_r2_pickup_window_computation() -> None:
    """R2: Earliest is landing + 60m, latest is landing + 24h."""
    landing = "2027-04-10T10:30"
    default_p, earliest_p, latest_p = compute_pickup_window(landing)
    assert default_p == "2027-04-10T11:30"
    assert earliest_p == "2027-04-10T11:30"
    assert latest_p == "2027-04-11T10:30"


def test_r2_pickup_too_early() -> None:
    """R2: Pickup earlier than landing + 60m raises R2 violation."""
    landing = "2027-04-10T10:30"
    with pytest.raises(RuleViolationException) as exc_info:
        validate_r2_pickup("2027-04-10T11:00", landing)  # only 30m after
    err = exc_info.value
    assert err.rule == "R2"
    assert err.field == "pickup_local"
    assert err.allowed["min"] == "2027-04-10T11:30"


def test_r2_pickup_days_later_is_allowed() -> None:
    """R2: the traveler may choose any pickup at least 60 minutes after landing."""
    validate_r2_pickup("2027-04-12T18:00", "2027-04-10T10:30")


def test_r3_price_in_range() -> None:
    """R3: Price within route range passes."""
    validate_r3_price(12000, 10200, 16800)
    validate_r3_price(10200, 10200, 16800)  # boundary min
    validate_r3_price(16800, 10200, 16800)  # boundary max


def test_r3_price_below_min() -> None:
    """R3: Price below minimum raises R3 violation with allowed range."""
    with pytest.raises(RuleViolationException) as exc_info:
        validate_r3_price(9000, 10200, 16800)
    err = exc_info.value
    assert err.rule == "R3"
    assert err.field == "price_inr"
    assert err.allowed == {"min": 10200, "max": 16800}


def test_busy_window_is_drive_there_and_back() -> None:
    """R6: a car is busy for twice the one-way drive, and the end is exclusive."""
    start, end = compute_ride_busy_interval("2027-04-10T11:30", 90)
    assert start == "2027-04-10T11:30"
    assert end == "2027-04-10T14:30"


def test_r1_child_age_zero_is_allowed() -> None:
    """R1: an infant aged 0 is a child and needs a seat."""
    validate_r1_request(
        arrival_airport="NRT",
        serves_cities=["Tokyo"],
        hotel_city="Tokyo",
        adults=1,
        child_ages=[0],
    )


def test_r1_negative_child_age() -> None:
    """R1: a negative age is refused."""
    with pytest.raises(RuleViolationException) as exc_info:
        validate_r1_request(
            arrival_airport="NRT",
            serves_cities=["Tokyo"],
            hotel_city="Tokyo",
            adults=1,
            child_ages=[-1],
        )
    assert exc_info.value.rule == "R1"
    assert exc_info.value.field == "child_ages"


def test_r2_pickup_exactly_60_minutes() -> None:
    """R2: pickup at landing + 60 minutes is allowed."""
    validate_r2_pickup("2027-04-10T11:30", "2027-04-10T10:30")


def test_r3_price_above_max() -> None:
    """R3: Price above maximum raises R3 violation."""
    with pytest.raises(RuleViolationException) as exc_info:
        validate_r3_price(20000, 10200, 16800)
    err = exc_info.value
    assert err.rule == "R3"
    assert err.field == "price_inr"
