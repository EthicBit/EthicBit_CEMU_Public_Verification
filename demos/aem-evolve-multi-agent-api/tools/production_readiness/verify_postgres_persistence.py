#!/usr/bin/env python3
"""
v2.0 PR 3 — PostgreSQL Production Persistence Verifier

Gate output: POSTGRES_PRODUCTION_PERSISTENCE_CHECK=PASS | FAIL

IMPORTANT: This gate FAILS when AEM_DB_URL is not configured.
That is the correct and expected outcome for a local/demo environment.
Set AEM_DB_URL to a real PostgreSQL instance and AEM_DB_ADAPTER=postgres
to satisfy this gate.

Mandatory evidence checked:
  C-01  AEM_DB_URL configured
  C-02  PostgresAdapter importable
  C-03  PostgreSQL connection reachable (ping)
  C-04  SQLite disabled (AEM_DB_ADAPTER != sqlite)
  C-05  Migrations applied successfully
  C-06  Schema validation PASS (all tables + columns)
  C-07  Connection pooling configured
  C-08  Concurrent writes (8-thread load test)
  C-09  Audit-chain integrity verified after concurrent writes
  C-10  Backup tooling available (pg_dump in PATH)
"""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DEMO_ROOT = Path(__file__).resolve().parents[2]
ASSURANCE_OUT = DEMO_ROOT.parents[1] / "assurance" / "evolve-multi-agent" / "v2_0"

if str(DEMO_ROOT) not in sys.path:
    sys.path.insert(0, str(DEMO_ROOT))

_CHECKS: list[dict[str, Any]] = []
_PASS = 0
_FAIL = 0


def _check(check_id: str, label: str, passed: bool, detail: str = "") -> None:
    global _PASS, _FAIL
    status = "PASS" if passed else "FAIL"
    if passed:
        _PASS += 1
    else:
        _FAIL += 1
    entry: dict[str, Any] = {"id": check_id, "label": label, "status": status}
    if detail:
        entry["detail"] = detail
    _CHECKS.append(entry)
    marker = "✓" if passed else "✗"
    print(f"  [{marker}] {check_id}: {label} — {status}" + (f" ({detail})" if detail else ""))


def run() -> str:
    print("=" * 70)
    print("v2.0 PR 3 — PostgreSQL Production Persistence Verifier")
    print("=" * 70)

    db_url = os.getenv("AEM_DB_URL", "").strip()
    db_adapter_env = os.getenv("AEM_DB_ADAPTER", "").strip()

    print(f"\nEnvironment:")
    print(f"  AEM_DB_URL      = {(db_url[:40] + '...') if len(db_url) > 40 else db_url or '(not set)'}")
    print(f"  AEM_DB_ADAPTER  = {db_adapter_env or '(not set)'}")
    print()

    # C-01: AEM_DB_URL configured
    _check("C-01", "AEM_DB_URL env var configured", bool(db_url),
           db_url[:40] if db_url else "AEM_DB_URL not set")

    # C-02: PostgresAdapter importable
    try:
        from db_adapter import PostgresAdapter
        _check("C-02", "PostgresAdapter importable", True)
    except ImportError as exc:
        _check("C-02", "PostgresAdapter importable", False, str(exc))
        _emit_report("FAIL", db_url, None)
        return "POSTGRES_PRODUCTION_PERSISTENCE_CHECK=FAIL"

    if not db_url:
        # Remaining checks are N/A without a DB URL
        _check("C-03", "PostgreSQL connection reachable N/A", True, "Skipped — AEM_DB_URL not set")
        _check("C-04", "SQLite disabled N/A", True, "Skipped")
        _check("C-05", "Migrations applied N/A", True, "Skipped")
        _check("C-06", "Schema validated N/A", True, "Skipped")
        _check("C-07", "Connection pooling N/A", True, "Skipped")
        _check("C-08", "Concurrent writes N/A", True, "Skipped")
        _check("C-09", "Audit-chain integrity N/A", True, "Skipped")
        _check("C-10", "Backup tooling N/A", True, "Skipped")
        _emit_honest_fail(db_url)
        return "POSTGRES_PRODUCTION_PERSISTENCE_CHECK=FAIL"

    # Load the gate object
    from db.postgres_production_gate import PostgresProductionGate
    gate = PostgresProductionGate(db_url)

    # C-03: Connection reachable
    conn_result = gate.check_connection()
    _check("C-03", "PostgreSQL connection reachable", conn_result["ok"],
           conn_result.get("detail", ""))

    if not conn_result["ok"]:
        for cid, label in [
            ("C-04", "SQLite disabled"),
            ("C-05", "Migrations applied"),
            ("C-06", "Schema validated"),
            ("C-07", "Connection pooling"),
            ("C-08", "Concurrent writes"),
            ("C-09", "Audit-chain integrity"),
            ("C-10", "Backup tooling"),
        ]:
            _check(cid, f"{label} N/A", False, "Skipped — DB not reachable")
        gate_status = "FAIL"
        _emit_report(gate_status, db_url, None)
        result_line = f"POSTGRES_PRODUCTION_PERSISTENCE_CHECK={gate_status}"
        print(f"\n  Gate result: {result_line} ({_PASS}/{_PASS + _FAIL})")
        return result_line

    # C-04: SQLite disabled
    sqlite_result = gate.check_sqlite_disabled()
    _check("C-04", "SQLite not active in production mode", sqlite_result["ok"],
           sqlite_result.get("detail", ""))

    # C-05: Migrations applied
    mig_result = gate.run_migrations()
    _check("C-05", "Migrations applied successfully", mig_result["ok"],
           mig_result.get("detail", ""))

    # C-06: Schema validation
    schema_result = gate.check_schema()
    _check("C-06", "Schema validation PASS", schema_result["ok"],
           schema_result.get("detail", ""))

    # C-07: Connection pooling
    pool_result = gate.check_connection_pool()
    _check("C-07", "Connection pooling configured", pool_result["ok"],
           pool_result.get("detail", ""))

    # C-08: Concurrent writes
    print("  Running 8-thread concurrent write load test...")
    conc_result = gate.check_concurrent_writes(n_threads=8)
    _check("C-08", "Concurrent writes (8 threads)", conc_result["ok"],
           conc_result.get("detail", ""))

    # C-09: Audit chain integrity
    chain_result = gate.check_audit_chain_integrity()
    _check("C-09", "Audit-chain integrity after concurrent writes", chain_result["ok"],
           chain_result.get("detail", ""))

    # C-10: Backup tooling
    backup_result = gate.check_backup_tooling()
    _check("C-10", "Backup tooling available (pg_dump)", backup_result["ok"],
           backup_result.get("detail", ""))

    gate_status = "PASS" if _FAIL == 0 else "FAIL"
    _emit_report(gate_status, db_url, gate)
    result_line = f"POSTGRES_PRODUCTION_PERSISTENCE_CHECK={gate_status}"
    print()
    print(f"  Gate result: {result_line} ({_PASS}/{_PASS + _FAIL} checks passed)")
    return result_line


def _emit_honest_fail(db_url: str) -> None:
    _emit_report("FAIL", db_url, None)
    print()
    print("  Gate result: POSTGRES_PRODUCTION_PERSISTENCE_CHECK=FAIL")
    print()
    print("  NOTE: This is the correct and expected result for a local/demo")
    print("  environment. To satisfy this gate, set:")
    print("    AEM_DB_URL=postgresql://user:pass@host:5432/dbname")
    print("    AEM_DB_ADAPTER=postgres")
    print("  pointing to a real PostgreSQL instance, then re-run.")


def _emit_report(gate_status: str, db_url: str, gate: Any) -> None:
    ASSURANCE_OUT.mkdir(parents=True, exist_ok=True)
    report = {
        "gate": "POSTGRES_PRODUCTION_PERSISTENCE_CHECK",
        "gate_version": "v2.0-PR3",
        "result": gate_status,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "environment": {
            "db_url_configured": bool(db_url),
            "db_url_prefix": db_url[:30] if db_url else None,
            "db_adapter_env": os.getenv("AEM_DB_ADAPTER", ""),
        },
        "checks": _CHECKS,
        "summary": {"total": len(_CHECKS), "passed": _PASS, "failed": _FAIL},
        "non_claims": [
            "This gate does not certify enterprise-scale database performance",
            "pgbouncer configuration requires separate infrastructure evidence",
            "Backup/restore schedule requires separate operational evidence",
            "This gate does not grant regulatory approval",
            "PASS requires a real PostgreSQL instance — not SQLite",
            "This gate is not production-ready by itself — one of 12 required gates",
        ],
    }
    if gate_status == "FAIL":
        report["fail_reason"] = (
            "AEM_DB_URL not configured — PostgreSQL instance required"
            if not db_url
            else "One or more checks failed"
        )
    out_path = ASSURANCE_OUT / "postgres_persistence_check_report.json"
    out_path.write_text(json.dumps(report, indent=2))
    print(f"\n  Assurance report: {out_path}")


if __name__ == "__main__":
    result = run()
    sys.exit(0 if "=PASS" in result else 1)
