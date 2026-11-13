"""Pytest configuration and shared fixtures for FlyNGo backend tests."""

from collections.abc import Generator
from pathlib import Path
import sqlite3
import sys

# Ensure project root is in sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import pytest
from fastapi.testclient import TestClient

import backend.app.config as app_config
from backend.app.db.connection import get_connection, get_db
from backend.app.db.init import init_db
from backend.app.db.refdata_loader import load_reference_data
from backend.app.db.seed import seed_open_requests
from backend.app.main import app


@pytest.fixture
def temp_db(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Generator[sqlite3.Connection, None, None]:
    """Provide a fresh, fully initialized temporary SQLite database for a test."""
    db_file = tmp_path / "test_flyngo.db"
    monkeypatch.setattr(app_config, "DB_PATH", str(db_file))

    conn = get_connection(str(db_file))
    init_db(conn)
    load_reference_data(conn)
    seed_open_requests(conn)

    # Override get_db dependency in FastAPI
    def override_get_db() -> Generator[sqlite3.Connection, None, None]:
        test_conn = get_connection(str(db_file))
        try:
            yield test_conn
        finally:
            test_conn.close()

    app.dependency_overrides[get_db] = override_get_db

    yield conn
    conn.close()
    app.dependency_overrides.pop(get_db, None)


@pytest.fixture
def client(temp_db: sqlite3.Connection) -> Generator[TestClient, None, None]:
    """TestClient configured with the temporary database."""
    with TestClient(app) as test_client:
        yield test_client
