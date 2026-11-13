"""Database connection management for FlyNGo."""

from collections.abc import Generator
from contextlib import contextmanager
import os
from pathlib import Path
import sqlite3

from backend.app import config
from backend.app.db.libsql_conn import NamedConnection


def get_connection(db_path: str | Path | None = None) -> sqlite3.Connection | NamedConnection:
    """Open the database.

    Local runs use the SQLite file. When Turso credentials are set and the
    caller did not ask for a specific file, bookings are stored in Turso so
    they survive a serverless restart.
    """
    turso_url = os.getenv("TURSO_DATABASE_URL")
    turso_token = os.getenv("TURSO_AUTH_TOKEN")
    if db_path is None and turso_url and turso_token:
        import libsql

        remote = libsql.connect(database=turso_url, auth_token=turso_token)
        return NamedConnection(remote)

    if db_path is None and os.getenv("VERCEL"):
        # The deployment filesystem is read-only. /tmp lasts for this instance only.
        path = "/tmp/flyngo.db"
    else:
        path = str(db_path or config.DB_PATH)
    # Ensure parent directory exists for file-based DBs
    if path != ":memory:":
        Path(path).parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(path, timeout=15.0, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


@contextmanager
def get_db_context(
    db_path: str | Path | None = None,
) -> Generator[sqlite3.Connection, None, None]:
    """Context manager for SQLite connections with auto-rollback on error."""
    conn = get_connection(db_path)
    try:
        yield conn
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def get_db() -> Generator[sqlite3.Connection, None, None]:
    """FastAPI dependency yielding an active SQLite connection."""
    conn = get_connection()
    try:
        yield conn
    finally:
        conn.close()
