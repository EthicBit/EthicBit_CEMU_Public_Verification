#!/usr/bin/env python3
"""
postgres_mock_integration_test.py — mock-based integration test for AsyncPostgresAdapter.

Simulates asyncpg pool behaviour without a live database so the test suite
can run in CI without PostgreSQL. Tests the adapter's interaction contract
with the underlying asyncpg pool.

Expected output: POSTGRES_MOCK_INTEGRATION=PASS
"""

from __future__ import annotations

import asyncio
import sys
import unittest.mock as mock
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(_ROOT))

from db_adapter import AsyncPostgresAdapter  # noqa: E402


class _MockRecord(dict):
    """Mimics asyncpg.Record as a plain dict."""


class _MockConnection:
    def __init__(self) -> None:
        self._calls: list[tuple] = []

    async def execute(self, sql: str, *args) -> str:
        self._calls.append(("execute", sql, args))
        return "INSERT 0 1"

    async def fetch(self, sql: str, *args) -> list:
        self._calls.append(("fetch", sql, args))
        return [_MockRecord(id=1, name="test")]

    async def fetchrow(self, sql: str, *args):
        self._calls.append(("fetchrow", sql, args))
        return _MockRecord(id=1, name="first")

    async def fetchval(self, sql: str, *args, column: int = 0):
        self._calls.append(("fetchval", sql, args))
        return 42

    async def __aenter__(self):
        return self

    async def __aexit__(self, *_):
        pass


class _MockPool:
    def __init__(self) -> None:
        self._conn = _MockConnection()
        self.closed = False

    def acquire(self):
        return self._conn

    async def close(self) -> None:
        self.closed = True


async def run_integration_tests() -> tuple[int, int]:
    checks: list[tuple[str, bool, str]] = []
    pool = _MockPool()
    adapter = AsyncPostgresAdapter(pool)

    async def check(name: str, coro) -> None:
        try:
            result = await coro
            checks.append((name, True, str(result)[:60]))
        except Exception as exc:
            checks.append((name, False, str(exc)[:60]))

    # T-01 execute
    await check("T-01-execute", adapter.execute("INSERT INTO events VALUES ($1)", "evt-001"))

    # T-02 fetch
    await check("T-02-fetch", adapter.fetch("SELECT * FROM events"))

    # T-03 fetchrow
    await check("T-03-fetchrow", adapter.fetchrow("SELECT * FROM events WHERE id=$1", 1))

    # T-04 fetchval
    await check("T-04-fetchval", adapter.fetchval("SELECT COUNT(*) FROM events"))

    # T-05 ping
    await check("T-05-ping", adapter.ping())

    # T-06 close
    await check("T-06-close", adapter.close())

    passed = 0
    for name, ok, detail in checks:
        status = "PASS" if ok else "FAIL"
        if ok:
            passed += 1
        print(f"  {status}  {name}" + (f"  — {detail}" if detail else ""))

    return passed, len(checks)


def main() -> int:
    print("AsyncPostgresAdapter Mock Integration Test")
    print("=" * 44)
    passed, total = asyncio.run(run_integration_tests())
    print()
    result = "PASS" if passed == total else "FAIL"
    print(f"POSTGRES_MOCK_INTEGRATION={result}  ({passed}/{total})")
    return 0 if result == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
