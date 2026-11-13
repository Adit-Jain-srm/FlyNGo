"""The API logger writes rule refusals to the rotating log file."""

import logging
from collections.abc import Generator
from logging.handlers import RotatingFileHandler
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from backend.app.log import configure_logging, get_logger


@pytest.fixture
def log_file(tmp_path: Path) -> Generator[Path, None, None]:
    """Point the app logger at a temporary file, then restore the previous file."""
    path = tmp_path / "flyngo.log"
    previous = getattr(get_logger(), "_flyngo_log_path", None)
    configure_logging(path)
    try:
        yield path
    finally:
        if previous is not None:
            configure_logging(previous)


def test_rule_refusal_is_written_to_the_log_file(
    client: TestClient,
    log_file: Path,
) -> None:
    """A refused price is a WARNING line in the log file, not only on the terminal."""
    logger = get_logger()
    assert any(isinstance(handler, RotatingFileHandler) for handler in logger.handlers)
    assert any(type(handler) is logging.StreamHandler for handler in logger.handlers)

    response = client.post(
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
            "price_inr": 9000,
        },
    )
    assert response.status_code == 422
    assert response.json()["rule"] == "R3"

    text = log_file.read_text(encoding="utf-8")
    assert "WARNING flyngo rule refused rule=R3" in text
    assert "field=price_inr" in text


def test_a_multiline_reason_stays_on_one_log_line(log_file: Path) -> None:
    """A newline in a reason must not look like a second event."""
    get_logger().info("change rejected reason=%s", "kept the car\nbooking unchanged")
    lines = log_file.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1
    assert "kept the car booking unchanged" in lines[0]
