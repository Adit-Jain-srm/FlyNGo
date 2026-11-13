"""libsql connection that returns named rows, like sqlite3.Row.

The hosted database speaks SQL the same way SQLite does, but each row arrives
as a tuple. The rest of the app reads columns by name, so this wrapper puts
that name lookup back.
"""

from collections.abc import Iterator, Mapping, Sequence
from typing import Any


class NamedRow(Mapping[str, Any]):
    """One result row. Supports row['name'] and row[0]."""

    def __init__(self, columns: Sequence[str], values: Sequence[Any]) -> None:
        self._columns = list(columns)
        self._values = tuple(values)
        self._by_name = {column: values[index] for index, column in enumerate(columns)}

    def __getitem__(self, key: str | int) -> Any:
        if isinstance(key, int):
            return self._values[key]
        return self._by_name[key]

    def __iter__(self) -> Iterator[str]:
        return iter(self._by_name)

    def __len__(self) -> int:
        return len(self._by_name)


class NamedCursor:
    """Cursor whose fetch methods return NamedRow values."""

    def __init__(self, raw: Any) -> None:
        self._raw = raw
        self._columns: list[str] = []

    def execute(self, sql: str, parameters: Sequence[Any] | None = None) -> "NamedCursor":
        if parameters is None:
            self._raw.execute(sql)
        else:
            self._raw.execute(sql, parameters)
        description = self._raw.description or ()
        self._columns = [column[0] for column in description]
        return self

    def executemany(self, sql: str, seq_of_parameters: Sequence[Sequence[Any]]) -> "NamedCursor":
        self._raw.executemany(sql, seq_of_parameters)
        return self

    def fetchone(self) -> NamedRow | None:
        row = self._raw.fetchone()
        if row is None:
            return None
        return self._wrap(row)

    def fetchall(self) -> list[NamedRow]:
        return [self._wrap(row) for row in self._raw.fetchall()]

    def __iter__(self) -> Iterator[NamedRow]:
        return iter(self.fetchall())

    @property
    def lastrowid(self) -> int | None:
        return self._raw.lastrowid

    @property
    def description(self) -> Any:
        return self._raw.description

    def _wrap(self, row: Sequence[Any]) -> NamedRow:
        if not self._columns:
            self._columns = [str(index) for index in range(len(row))]
        return NamedRow(self._columns, row)


class NamedConnection:
    """DB-API connection over libsql with named rows and full script execution."""

    def __init__(self, raw: Any) -> None:
        self._raw = raw

    def cursor(self) -> NamedCursor:
        return NamedCursor(self._raw.cursor())

    def execute(self, sql: str, parameters: Sequence[Any] | None = None) -> NamedCursor:
        return self.cursor().execute(sql, parameters)

    def executemany(self, sql: str, seq_of_parameters: Sequence[Sequence[Any]]) -> NamedCursor:
        return self.cursor().executemany(sql, seq_of_parameters)

    def executescript(self, script: str) -> None:
        for statement in _sql_statements(script):
            self._raw.execute(statement)
        self._raw.commit()

    def commit(self) -> None:
        self._raw.commit()

    def rollback(self) -> None:
        self._raw.rollback()

    def close(self) -> None:
        self._raw.close()


def _sql_statements(script: str) -> list[str]:
    """Split a DDL script into statements. Line comments are removed first."""
    lines: list[str] = []
    for line in script.splitlines():
        if line.strip().startswith("--"):
            continue
        lines.append(line)
    return [statement.strip() for statement in "\n".join(lines).split(";") if statement.strip()]
