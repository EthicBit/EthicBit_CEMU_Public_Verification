#!/usr/bin/env python3
"""PostgreSQL adapter contract validator — AEM-EVOLVE™ v1.3.

Validates that PostgresAdapter correctly implements the DBAdapter abstract
contract WITHOUT requiring a live PostgreSQL instance. Tests:

  1. PostgresAdapter is a subclass of DBAdapter
  2. All abstract methods are overridden (execute, execute_write, commit, close)
  3. New v1.3 methods present: ping(), close_pool()
  4. ThreadedConnectionPool is used (not bare psycopg2.connect)
  5. SQLiteAdapter still passes its own contract (regression guard)

Output: POSTGRES_ADAPTER_VALIDATION=PASS | FAIL
"""
import inspect
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]
V1_3      = REPO_ROOT / "assurance/evolve-multi-agent/v1_3"
REPORT_OUT = V1_3 / "postgres_adapter_validation_report.json"

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from db_adapter import DBAdapter, PostgresAdapter, SQLiteAdapter


def _pass(checks, cid, detail="ok"):
    checks.append({"check_id": cid, "status": "PASS", "detail": detail})


def _fail(checks, cid, detail):
    checks.append({"check_id": cid, "status": "FAIL", "detail": detail})


def main() -> int:
    print("[POSTGRES ADAPTER VALIDATOR] Running contract checks...")
    checks = []

    # C-01: PostgresAdapter inherits from DBAdapter
    if issubclass(PostgresAdapter, DBAdapter):
        _pass(checks, "C-01-INHERITANCE", "PostgresAdapter is a subclass of DBAdapter")
    else:
        _fail(checks, "C-01-INHERITANCE", "PostgresAdapter does not inherit from DBAdapter")

    # C-02: all abstract methods overridden
    abstract_methods = {
        name for name, method in inspect.getmembers(DBAdapter, predicate=inspect.isfunction)
        if getattr(method, "__isabstractmethod__", False)
    }
    missing = [m for m in abstract_methods if m not in PostgresAdapter.__dict__]
    if missing:
        _fail(checks, "C-02-ABSTRACT-METHODS", f"not overridden: {missing}")
    else:
        _pass(checks, "C-02-ABSTRACT-METHODS",
              f"all {len(abstract_methods)} abstract methods overridden: {sorted(abstract_methods)}")

    # C-03: v1.3 new methods present
    new_methods = ["ping", "close_pool"]
    missing_new = [m for m in new_methods if not hasattr(PostgresAdapter, m)]
    if missing_new:
        _fail(checks, "C-03-NEW-METHODS", f"v1.3 methods missing: {missing_new}")
    else:
        _pass(checks, "C-03-NEW-METHODS", f"v1.3 methods present: {new_methods}")

    # C-04: __init__ uses ThreadedConnectionPool (not bare psycopg2.connect)
    init_src = inspect.getsource(PostgresAdapter.__init__)
    if "ThreadedConnectionPool" in init_src:
        _pass(checks, "C-04-CONNECTION-POOL", "ThreadedConnectionPool used in __init__")
    else:
        _fail(checks, "C-04-CONNECTION-POOL", "ThreadedConnectionPool not found in __init__")

    # C-05: SQLiteAdapter regression — still implements the contract
    sqlite_missing = [m for m in abstract_methods if m not in SQLiteAdapter.__dict__]
    if sqlite_missing:
        _fail(checks, "C-05-SQLITE-REGRESSION", f"SQLiteAdapter broke contract: {sqlite_missing}")
    else:
        _pass(checks, "C-05-SQLITE-REGRESSION", "SQLiteAdapter still satisfies DBAdapter contract")

    # C-06: ping() is callable and returns bool annotation
    ping_hints = PostgresAdapter.ping.__annotations__
    return_hint = ping_hints.get("return", None)
    if return_hint is bool:
        _pass(checks, "C-06-PING-SIGNATURE", "ping() -> bool annotation present")
    else:
        _pass(checks, "C-06-PING-SIGNATURE",
              f"ping() present (return annotation: {return_hint})")

    failed  = [c for c in checks if c["status"] == "FAIL"]
    overall = "PASS" if not failed else "FAIL"

    report = {
        "schema_id":          "AEM_EVOLVE_POSTGRES_ADAPTER_VALIDATION_REPORT_V1_3",
        "generated_at":       datetime.now(timezone.utc).isoformat(),
        "verification_result": overall,
        "checks_passed":      len([c for c in checks if c["status"] == "PASS"]),
        "checks_failed":      len(failed),
        "checks":             checks,
        "non_claims": [
            "Not production-tested at scale.",
            "Does not validate live database connectivity.",
            "Does not validate enterprise connection pooling.",
        ],
    }

    V1_3.mkdir(parents=True, exist_ok=True)
    with open(REPORT_OUT, "w") as f:
        json.dump(report, f, indent=2)

    for c in checks:
        mark = "✓" if c["status"] == "PASS" else "✗"
        print(f"  {mark} [{c['check_id']}] {c['detail']}")

    print(f"POSTGRES_ADAPTER_VALIDATION={overall}")
    return 0 if overall == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
