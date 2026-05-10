#!/usr/bin/env python3
"""
v2.0 PR 4 — Migration and Recovery Evidence Verifier

Gate output: MIGRATION_RECOVERY_CHECK=PASS | FAIL

IMPORTANT: This gate FAILS when AEM_DB_URL is not configured.
That is the correct and expected outcome for a local/demo environment.
Set AEM_DB_URL to a real PostgreSQL instance to satisfy this gate.

Mandatory evidence checked:
  C-01  AEM_DB_URL configured
  C-02  MigrationRecoveryEvidence importable
  C-03  Rollback migration files exist and are hashed
  C-04  Forward migration hash before/after recorded
  C-05  Rollback simulation evidence produced
  C-06  Receipt/event count reconciliation PASS
  C-07  Audit-chain continuity verified
  C-08  Backup tooling available (pg_dump)
  C-09  Backup file produced and hashed
  C-10  Restore verification PASS (dump content verified)
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
ROLLBACK_DIR = DEMO_ROOT / "migrations" / "rollback"

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
    print("v2.0 PR 4 — Migration and Recovery Evidence Verifier")
    print("=" * 70)

    db_url = os.getenv("AEM_DB_URL", "").strip()

    print(f"\nEnvironment:")
    print(f"  AEM_DB_URL = {(db_url[:40] + '...') if len(db_url) > 40 else db_url or '(not set)'}")
    print()

    # C-01: AEM_DB_URL configured
    _check("C-01", "AEM_DB_URL env var configured", bool(db_url),
           db_url[:40] if db_url else "AEM_DB_URL not set")

    # C-02: MigrationRecoveryEvidence importable
    try:
        from db.migration_recovery_evidence import MigrationRecoveryEvidence, ROLLBACK_DIR as RBD
        _check("C-02", "db.migration_recovery_evidence importable", True)
    except ImportError as exc:
        _check("C-02", "db.migration_recovery_evidence importable", False, str(exc))
        _emit_report("FAIL", db_url, None)
        return "MIGRATION_RECOVERY_CHECK=FAIL"

    # C-03: Rollback migration files exist (file-system check — no DB needed)
    rollback_files = sorted(ROLLBACK_DIR.glob("*.sql")) if ROLLBACK_DIR.exists() else []
    rb_hashes = {f.name: __import__("hashlib").sha256(f.read_bytes()).hexdigest() for f in rollback_files}
    _check("C-03", "Rollback migration files exist and hashed",
           len(rollback_files) >= 1,
           f"{len(rollback_files)} file(s): {', '.join(rb_hashes.keys())}" if rollback_files
           else "no rollback files in migrations/rollback/")

    if not db_url:
        for cid, label in [
            ("C-04", "Forward migration hash before/after"),
            ("C-05", "Rollback simulation evidence"),
            ("C-06", "Count reconciliation PASS"),
            ("C-07", "Audit-chain continuity"),
            ("C-08", "Backup tooling available"),
            ("C-09", "Backup file produced"),
            ("C-10", "Restore verification PASS"),
        ]:
            _check(cid, f"{label} N/A", False, "Skipped — AEM_DB_URL not set")
        _emit_honest_fail(db_url, rb_hashes)
        return "MIGRATION_RECOVERY_CHECK=FAIL"

    # Run full evidence generation
    from db.migration_recovery_evidence import MigrationRecoveryEvidence
    evidence_obj = MigrationRecoveryEvidence(db_url)

    print("  Generating migration and recovery evidence...")
    evidence = evidence_obj.generate_evidence()

    ev = evidence.get("evidence", {})

    # C-04: Forward migration hash before/after
    fwd = ev.get("forward_migration", {})
    _check("C-04", "Forward migration hash before/after recorded",
           fwd.get("ok", False),
           f"before={fwd.get('before_hash', '?')[:12]}... after={fwd.get('after_hash', '?')[:12]}..."
           if fwd.get("ok") else fwd.get("detail", "failed"))

    # C-05: Rollback simulation evidence
    rbk = ev.get("rollback_migration", {})
    _check("C-05", "Rollback simulation evidence produced",
           rbk.get("ok", False),
           f"{len(rbk.get('rollback_files', []))} rollback file(s) hashed"
           if rbk.get("ok") else rbk.get("detail", "failed"))

    # C-06: Count reconciliation
    recon = ev.get("count_reconciliation", {})
    _check("C-06", "Receipt/event count reconciliation PASS",
           recon.get("ok", False),
           recon.get("detail", ""))

    # C-07: Audit-chain continuity
    chain = ev.get("audit_chain_continuity", {})
    _check("C-07", "Audit-chain continuity verified",
           chain.get("ok", False),
           chain.get("detail", ""))

    # C-08: Backup tooling
    backup = ev.get("backup_test", {})
    pg_dump_ok = backup.get("ok", False) or "not found" not in backup.get("detail", "not found")
    import shutil as _shutil
    pg_dump_path = _shutil.which("pg_dump")
    _check("C-08", "Backup tooling available (pg_dump)",
           pg_dump_path is not None,
           f"pg_dump at {pg_dump_path}" if pg_dump_path else "pg_dump not in PATH")

    # C-09: Backup file produced
    _check("C-09", "Backup file produced and hashed",
           backup.get("ok", False),
           backup.get("detail", "pg_dump failed"))

    # C-10: Restore verification
    restore = ev.get("restore_verification", {})
    _check("C-10", "Restore verification PASS (dump content checked)",
           restore.get("ok", False),
           restore.get("detail", ""))

    gate_status = "PASS" if _FAIL == 0 else "FAIL"
    _emit_report(gate_status, db_url, evidence)
    result_line = f"MIGRATION_RECOVERY_CHECK={gate_status}"
    print()
    print(f"  Gate result: {result_line} ({_PASS}/{_PASS + _FAIL} checks passed)")
    return result_line


def _emit_honest_fail(db_url: str, rb_hashes: dict) -> None:
    _emit_report("FAIL", db_url, {"rollback_file_hashes": rb_hashes})
    print()
    print("  Gate result: MIGRATION_RECOVERY_CHECK=FAIL")
    print()
    print("  NOTE: This is the correct and expected result for a local/demo")
    print("  environment. To satisfy this gate, set:")
    print("    AEM_DB_URL=postgresql://user:pass@host:5432/dbname")
    print("  pointing to a real PostgreSQL instance, then re-run.")


def _emit_report(gate_status: str, db_url: str, evidence: Any) -> None:
    ASSURANCE_OUT.mkdir(parents=True, exist_ok=True)
    report = {
        "gate": "MIGRATION_RECOVERY_CHECK",
        "gate_version": "v2.0-PR4",
        "result": gate_status,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "environment": {
            "db_url_configured": bool(db_url),
            "db_url_prefix": db_url[:30] if db_url else None,
        },
        "checks": _CHECKS,
        "summary": {"total": len(_CHECKS), "passed": _PASS, "failed": _FAIL},
        "evidence": evidence or {},
        "non_claims": [
            "Full restore evidence requires a secondary PostgreSQL instance",
            "Not disaster recovery complete by itself",
            "Not zero data loss unless RPO evidence separately supports it",
            "This gate does not grant regulatory approval",
            "This gate is not production-ready by itself — one of 12 required gates",
        ],
    }
    if gate_status == "FAIL":
        report["fail_reason"] = (
            "AEM_DB_URL not configured — PostgreSQL instance required"
            if not db_url
            else "One or more checks failed"
        )
    out_path = ASSURANCE_OUT / "migration_recovery_check_report.json"
    out_path.write_text(json.dumps(report, indent=2))
    print(f"\n  Assurance report: {out_path}")


if __name__ == "__main__":
    result = run()
    sys.exit(0 if "=PASS" in result else 1)
