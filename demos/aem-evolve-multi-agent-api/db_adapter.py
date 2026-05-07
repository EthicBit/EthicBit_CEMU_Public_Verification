"""
AEM-EVOLVE Multi-Agent Governance API — Database Adapter Interface.

Defines an abstract DBAdapter that the API can use instead of calling
sqlite3 directly.  The SQLiteAdapter below is the demo implementation.
A future PostgresAdapter (or any other DBAPI-2 backend) can be dropped in
without touching main.py by setting the AEM_DB_ADAPTER env-var and
passing a concrete instance to build_graph().

Migration path to PostgreSQL
-----------------------------
1. Install psycopg2 or asyncpg + SQLAlchemy.
2. Implement PostgresAdapter (extend DBAdapter, swap sqlite3 → psycopg2 calls).
3. Export AEM_DB_URL=postgresql://user:pass@host:5432/dbname
4. In main.py replace SQLiteAdapter() with PostgresAdapter(os.environ["AEM_DB_URL"]).

Non-claims
----------
- This module does NOT provide a production-ready connection pool.
- This module does NOT provide async I/O (SQLiteAdapter is synchronous).
- The migration path is documented guidance, not a tested implementation.
"""

from __future__ import annotations

import sqlite3
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any


class DBAdapter(ABC):
    """Minimal persistence interface for AEM-EVOLVE audit tables."""

    @abstractmethod
    def execute(self, sql: str, params: tuple = ()) -> list[tuple[Any, ...]]:
        """Execute a statement and return all rows (empty list for non-SELECT)."""

    @abstractmethod
    def execute_write(self, sql: str, params: tuple = ()) -> None:
        """Execute a write statement (INSERT/UPDATE/CREATE TABLE)."""

    @abstractmethod
    def commit(self) -> None:
        """Commit the current transaction."""

    @abstractmethod
    def close(self) -> None:
        """Release the underlying connection."""


class SQLiteAdapter(DBAdapter):
    """DBAdapter backed by a local SQLite file (demo use only)."""

    def __init__(self, db_path: Path | str) -> None:
        self._conn = sqlite3.connect(str(db_path), check_same_thread=False)

    def execute(self, sql: str, params: tuple = ()) -> list[tuple[Any, ...]]:
        cursor = self._conn.cursor()
        cursor.execute(sql, params)
        return cursor.fetchall()

    def execute_write(self, sql: str, params: tuple = ()) -> None:
        cursor = self._conn.cursor()
        cursor.execute(sql, params)

    def commit(self) -> None:
        self._conn.commit()

    def close(self) -> None:
        self._conn.close()

    @property
    def raw_connection(self) -> sqlite3.Connection:
        """Expose raw sqlite3.Connection for callers that need it (e.g. LangGraph SqliteSaver)."""
        return self._conn
