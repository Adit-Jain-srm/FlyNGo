import pytest
libsql = pytest.importorskip("libsql")

from backend.app.db.init import init_db
from backend.app.db.libsql_conn import NamedConnection


def test_named_connection_runs_schema_and_reads_by_column_name() -> None:
    """init_db can create every table, and a row can be read by name or index."""
    connection = NamedConnection(libsql.connect(":memory:"))
    init_db(connection)

    connection.execute(
        "INSERT INTO airports (code, name, city, country, timezone) VALUES (?, ?, ?, ?, ?)",
        ("AUH", "Zayed International Airport", "Abu Dhabi", "AE", "Asia/Dubai"),
    )
    connection.commit()

    row = connection.execute("SELECT code, name FROM airports WHERE code = ?", ("AUH",)).fetchone()
    assert row is not None
    assert row["name"] == "Zayed International Airport"
    assert row[0] == "AUH"
    assert dict(row)["code"] == "AUH"

    tables = {
        item[0]
        for item in connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'"
        ).fetchall()
    }
    assert {"flights", "hotels", "bookings", "offers", "change_requests"} <= tables
    connection.execute("PRAGMA foreign_keys = ON;")
    mode = connection.execute("PRAGMA foreign_keys").fetchone()
    assert mode is not None
    assert mode[0] == 1
    connection.close()
