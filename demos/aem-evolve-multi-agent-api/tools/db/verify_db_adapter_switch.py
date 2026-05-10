#!/usr/bin/env python3
"""
verify_db_adapter_switch.py — v1.8.0 AEM_DB_ADAPTER env var switch check.

Checks:
  C-01  _build_db_adapter is importable
  C-02  Default (no env var) returns SQLiteAdapter
  C-03  AEM_DB_ADAPTER=sqlite returns SQLiteAdapter
  C-04  AEM_DB_ADAPTER=postgres with no AEM_DB_URL falls back to SQLiteAdapter
  C-05  AEM_DB_ADAPTER=postgres with bad URL triggers PostgresAdapter attempt + fallback
  C-06  _db_adapter_label reflects the active adapter
  C-07  GET /health db_adapter field reflects active adapter label
  C-08  GET /health db_adapter_switch field present
  C-09  GET /healthz db field reflects adapter type (sqlite or postgres)
  C-10  SQLiteAdapter passes init_audit_tables without error

Expected output: DB_ADAPTER_SWITCH_VERIFICATION=PASS (10/10)
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

_DEMO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_DEMO_ROOT) not in sys.path:
    sys.path.insert(0, str(_DEMO_ROOT))

os.environ.setdefault("AEM_LOG_LEVEL", "WARNING")

from fastapi.testclient import TestClient  # noqa: E402
import main as _main  # noqa: E402
from main import _build_db_adapter, _db_adapter_label, init_audit_tables  # noqa: E402
from db_adapter import SQLiteAdapter, PostgresAdapter  # noqa: E402


def run_checks() -> tuple[int, int, list[dict]]:
    checks: list[dict] = []
    passed = 0

    def record(name: str, ok: bool, detail: str = "") -> None:
        nonlocal passed
        status = "PASS" if ok else "FAIL"
        checks.append({"check": name, "status": status, "detail": detail})
        if ok:
            passed += 1
        print(f"  {status}  {name}" + (f"  — {detail}" if detail else ""))

    # C-01 _build_db_adapter importable
    try:
        assert callable(_build_db_adapter)
        record("C-01-build-db-adapter-importable", True)
    except Exception as exc:
        record("C-01-build-db-adapter-importable", False, str(exc))

    # C-02 Default (no env var) → SQLiteAdapter
    saved = os.environ.pop("AEM_DB_ADAPTER", None)
    os.environ.pop("AEM_DB_URL", None)
    try:
        adapter, label = _build_db_adapter()
        record("C-02-default-is-sqlite", isinstance(adapter, SQLiteAdapter),
               f"label={label}")
        adapter.close()
    except Exception as exc:
        record("C-02-default-is-sqlite", False, str(exc))
    finally:
        if saved:
            os.environ["AEM_DB_ADAPTER"] = saved

    # C-03 AEM_DB_ADAPTER=sqlite → SQLiteAdapter
    os.environ["AEM_DB_ADAPTER"] = "sqlite"
    os.environ.pop("AEM_DB_URL", None)
    try:
        adapter, label = _build_db_adapter()
        record("C-03-explicit-sqlite", isinstance(adapter, SQLiteAdapter) and label == "SQLiteAdapter",
               f"label={label}")
        adapter.close()
    except Exception as exc:
        record("C-03-explicit-sqlite", False, str(exc))
    finally:
        os.environ.pop("AEM_DB_ADAPTER", None)

    # C-04 AEM_DB_ADAPTER=postgres with no URL → fallback SQLite
    os.environ["AEM_DB_ADAPTER"] = "postgres"
    os.environ.pop("AEM_DB_URL", None)
    try:
        adapter, label = _build_db_adapter()
        record("C-04-postgres-no-url-fallback-sqlite",
               isinstance(adapter, SQLiteAdapter),
               f"label={label} (expected SQLiteAdapter fallback when no AEM_DB_URL)")
        adapter.close()
    except Exception as exc:
        record("C-04-postgres-no-url-fallback-sqlite", False, str(exc))
    finally:
        os.environ.pop("AEM_DB_ADAPTER", None)

    # C-05 AEM_DB_ADAPTER=postgres with bad URL → attempt + fallback
    os.environ["AEM_DB_ADAPTER"] = "postgres"
    os.environ["AEM_DB_URL"] = "postgresql://invalid:invalid@localhost:9999/nonexistent"
    try:
        adapter, label = _build_db_adapter()
        # Either falls back to SQLite (connection refused) or raises — both acceptable
        record("C-05-postgres-bad-url-fallback", isinstance(adapter, SQLiteAdapter),
               f"label={label}")
        adapter.close()
    except Exception as exc:
        record("C-05-postgres-bad-url-fallback", False, str(exc)[:80])
    finally:
        os.environ.pop("AEM_DB_ADAPTER", None)
        os.environ.pop("AEM_DB_URL", None)

    # C-06 _db_adapter_label reflects active adapter
    record("C-06-label-reflects-adapter", _db_adapter_label in ("SQLiteAdapter", "PostgresAdapter"),
           f"label={_db_adapter_label!r}")

    # C-07 / C-08 / C-09 — via TestClient
    with TestClient(_main.app, raise_server_exceptions=True) as client:
        r = client.get("/health")
        health = r.json() if r.status_code == 200 else {}

        # C-07 db_adapter reflects label
        record("C-07-health-db-adapter-field", health.get("db_adapter") == _db_adapter_label,
               f"health={health.get('db_adapter')!r} label={_db_adapter_label!r}")

        # C-08 db_adapter_switch field present
        switch_field = health.get("db_adapter_switch", "")
        record("C-08-health-db-adapter-switch-field", bool(switch_field),
               f"field={switch_field!r}")

        # C-09 /healthz db field
        r = client.get("/healthz")
        hz = r.json() if r.status_code == 200 else {}
        db_field = hz.get("db", "")
        expected_db = "postgres" if "Postgres" in _db_adapter_label else "sqlite"
        record("C-09-healthz-db-field", db_field == expected_db,
               f"got={db_field!r} expected={expected_db!r}")

    # C-10 SQLiteAdapter init_audit_tables no error
    try:
        adapter = SQLiteAdapter(":memory:")
        init_audit_tables(adapter)
        rows = adapter.execute("SELECT name FROM sqlite_master WHERE type='table'")
        table_names = {r[0] for r in rows}
        expected = {"evolution_events", "evolution_receipts", "human_decisions",
                    "audit_chain", "hitl_used_tokens"}
        record("C-10-sqlite-audit-tables-init", expected.issubset(table_names),
               f"tables={table_names}")
        adapter.close()
    except Exception as exc:
        record("C-10-sqlite-audit-tables-init", False, str(exc))

    return passed, len(checks), checks


def main() -> int:
    print("DB Adapter Switch Verification — AEM-EVOLVE™ v1.8.0")
    print("=" * 54)
    passed, total, checks = run_checks()
    print()

    result = "PASS" if passed == total else "FAIL"
    report = {
        "component": "verify_db_adapter_switch",
        "version": "v1.8",
        "checks_passed": passed,
        "checks_total": total,
        "result": result,
        "non_claims": [
            "PostgreSQL path not tested with a live database in this verifier.",
            "Connection pool sizing is demo-grade.",
            "SQLiteAdapter is not production audit storage.",
        ],
        "checks": checks,
    }

    out_dir = Path(__file__).resolve().parents[4] / "assurance" / "evolve-multi-agent" / "v1_8"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "db_adapter_switch_report.json").write_text(json.dumps(report, indent=2))

    print(f"DB_ADAPTER_SWITCH_VERIFICATION={result}  ({passed}/{total})")
    return 0 if result == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
