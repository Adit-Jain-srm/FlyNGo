"""Database connection management for FlyNGo."""

from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path
import sqlite3

from backend.app import config


def get_connection(db_path: str | Path | None = None) -> sqlite3.Connection:
    """Create and configure a new SQLite connection.

    Always enables foreign keys and sets row_factory to sqlite3.Row.
    """
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
