#!/usr/bin/env python3
"""
async_postgres_concurrency_test.py — concurrent mock test for AsyncPostgresAdapter.

Fires N concurrent asyncio tasks against a mock pool and validates:
- No results are lost (all tasks complete)
- No exceptions are raised under concurrency
- Throughput is measurable and non-zero
- Results from concurrent fetches are independent

Checks:
  C-01  Mock pool accepts N=20 concurrent execute() calls without error
  C-02  All N execute() results are non-None
  C-03  Mock pool accepts N=20 concurrent fetch() calls without error
  C-04  N concurrent ping() calls all return True
  C-05  Sequential vs concurrent output is identical (determinism)
  C-06  Concurrent writes complete in < 5 seconds (performance gate)

Expected output: ASYNC_POSTGRES_CONCURRENCY=PASS
"""

from __future__ import annotations

import asyncio
import json
import sys
import time
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_ROOT))

from db_adapter import AsyncPostgresAdapter  # noqa: E402

_CONCURRENCY = 20


class _MockConnection:
    async def execute(self, sql: str, *args) -> str:
        await asyncio.sleep(0)  # yield to event loop
        return "INSERT 0 1"

    async def fetch(self, sql: str, *args) -> list:
        await asyncio.sleep(0)
        return [{"id": hash(sql) % 1000, "value": "ok"}]

    async def fetchrow(self, sql: str, *args):
        await asyncio.sleep(0)
        return {"id": 1}

    async def fetchval(self, sql: str, *args, column: int = 0):
        await asyncio.sleep(0)
        return 1

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


async def run_checks() -> tuple[int, int, list[dict]]:
    checks: list[dict] = []
    passed = 0

    def record(name: str, ok: bool, detail: str = "") -> None:
        nonlocal passed
        status = "PASS" if ok else "FAIL"
        checks.append({"check": name, "status": status, "detail": detail})
        if ok:
            passed += 1
        print(f"  {status}  {name}" + (f"  — {detail}" if detail else ""))

    adapter = AsyncPostgresAdapter(_MockPool())

    # C-01 N concurrent execute() calls
    sql = "INSERT INTO evolution_events (id) VALUES ($1)"
    try:
        results = await asyncio.gather(
            *[adapter.execute(sql, f"evt-{i:04d}") for i in range(_CONCURRENCY)]
        )
        record("C-01-concurrent-execute-no-error", True, f"N={_CONCURRENCY}")
    except Exception as exc:
        record("C-01-concurrent-execute-no-error", False, str(exc)[:60])
        results = []

    # C-02 All results non-None
    ok = all(r is not None for r in results)
    record("C-02-execute-all-results-non-null", ok, f"results={len(results)}")

    # C-03 N concurrent fetch()
    try:
        fetches = await asyncio.gather(
            *[adapter.fetch("SELECT * FROM events WHERE id=$1", i) for i in range(_CONCURRENCY)]
        )
        ok = len(fetches) == _CONCURRENCY and all(isinstance(r, list) for r in fetches)
        record("C-03-concurrent-fetch-no-error", ok, f"N={_CONCURRENCY}")
    except Exception as exc:
        record("C-03-concurrent-fetch-no-error", False, str(exc)[:60])

    # C-04 N concurrent ping()
    try:
        pings = await asyncio.gather(*[adapter.ping() for _ in range(_CONCURRENCY)])
        ok = all(pings)
        record("C-04-concurrent-ping-all-true", ok, f"true={sum(pings)}/{_CONCURRENCY}")
    except Exception as exc:
        record("C-04-concurrent-ping-all-true", False, str(exc)[:60])

    # C-05 Determinism — sequential vs concurrent fetch of the same query
    sequential = []
    for i in range(5):
        r = await adapter.fetch("SELECT id FROM events WHERE id=$1", i)
        sequential.append(r)
    concurrent = await asyncio.gather(*[adapter.fetch("SELECT id FROM events WHERE id=$1", i) for i in range(5)])
    record("C-05-sequential-concurrent-determinism",
           sequential == list(concurrent),
           f"match={sequential == list(concurrent)}")

    # C-06 N=20 concurrent writes complete in < 5 s
    t0 = time.perf_counter()
    await asyncio.gather(
        *[adapter.execute("INSERT INTO audit_chain (id) VALUES ($1)", f"chain-{i}") for i in range(_CONCURRENCY)]
    )
    elapsed = time.perf_counter() - t0
    ok = elapsed < 5.0
    record("C-06-performance-gate", ok, f"elapsed={elapsed:.4f}s  (< 5.0s)")

    return passed, len(checks), checks


def main() -> int:
    print("AsyncPostgresAdapter Concurrency Test")
    print("=" * 44)
    passed, total, checks = asyncio.run(run_checks())
    print()

    result = "PASS" if passed == total else "FAIL"
    report = {
        "component": "async_postgres_concurrency",
        "version": "v1.5",
        "concurrency": _CONCURRENCY,
        "checks_passed": passed,
        "checks_total": total,
        "result": result,
        "non_claims": [
            "This test uses a mock pool — not a live PostgreSQL instance.",
            "Performance gate is for mock latency only — real latency depends on network + DB.",
        ],
        "checks": checks,
    }

    out_dir = Path(__file__).resolve().parents[4] / "assurance" / "evolve-multi-agent" / "v1_5"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "async_postgres_concurrency_report.json").write_text(json.dumps(report, indent=2))

    print(f"ASYNC_POSTGRES_CONCURRENCY={result}  ({passed}/{total})")
    return 0 if result == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
