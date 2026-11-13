"""Database schema initialization."""

from pathlib import Path
import sqlite3

from backend.app.db.connection import get_connection

SCHEMA_PATH = Path(__file__).resolve().parent / "schema.sql"


def init_db(conn: sqlite3.Connection | None = None) -> None:
    """Execute the schema DDL against the database."""
    should_close = False
    if conn is None:
        conn = get_connection()
        should_close = True

    try:
        with open(SCHEMA_PATH, encoding="utf-8") as f:
            schema_sql = f.read()
        conn.executescript(schema_sql)
        columns = {row[1] for row in conn.execute("PRAGMA table_info(offers)")}
        if "expires_at" not in columns:
            conn.execute("ALTER TABLE offers ADD COLUMN expires_at TEXT")
        conn.commit()
    finally:
        if should_close:
            conn.close()
