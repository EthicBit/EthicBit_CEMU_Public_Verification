#!/usr/bin/env python3
"""
AEM-EVOLVE™ v2.0 PR 11 — Rollback Procedure Evidence Gate Verifier.

Usage:
    python tools/production_readiness/verify_rollback_procedure.py

Set AEM_ROLLBACK_TESTER and AEM_ROLLBACK_TEST_DATE for full PASS.

Exit code:
    0 = PASS
    1 = FAIL (expected in local/demo — rollback dry-run not yet executed with tester identity)
"""
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

DEMO_ROOT = Path(__file__).resolve().parents[2]
if str(DEMO_ROOT) not in sys.path:
    sys.path.insert(0, str(DEMO_ROOT))

from rollback.rollback_gate import RollbackGate

_CHECKS = [
    ("C-01", "runbook",              "Rollback runbook (ROLLBACK_RUNBOOK.md) exists"),
    ("C-02", "runbook_steps",        "Runbook covers all 7 rollback steps"),
    ("C-03", "db_rollback_scripts",  "All 3 database rollback SQL scripts exist"),
    ("C-04", "gate_coverage",        "Runbook covers all 9 gate failure scenarios (PR1-PR9)"),
    ("C-05", "container_rollback",   "Container rollback procedure documented (docker/kubectl)"),
    ("C-06", "test_evidence",        "Rollback test evidence artifact with SHA256 and ≥5 scenarios"),
    ("C-07", "scenarios_passed",     "All 5 rollback dry-run scenarios passed"),
    ("C-08", "artifact_fingerprint", "Rollback test evidence artifact SHA256 fingerprint recorded"),
    ("C-09", "rollback_tester",      "Rollback dry-run tester identity (AEM_ROLLBACK_TESTER)"),
    ("C-10", "rollback_test_date",   "Rollback dry-run test date (AEM_ROLLBACK_TEST_DATE)"),
]


def _fmt(ok: bool, skipped: bool = False) -> str:
    if skipped:
        return "SKIP"
    return "PASS" if ok else "FAIL"


def main() -> int:
    gate = RollbackGate.from_env()
    result = gate.gate_check()
    checks = result["checks"]

    print("=" * 70)
    print("AEM-EVOLVE™ v2.0 PR 11 — Rollback Procedure Gate")
    print("=" * 70)
    print(f"Rollback tester   : {gate._rollback_tester or '(not set)'}")
    print(f"Rollback test date: {gate._rollback_test_date or '(not set)'}")
    print(f"Rollback tested   : {result['rollback_tested']}")
    print()

    for code, key, description in _CHECKS:
        full_key = f"{code}_{key}"
        c = checks.get(full_key, {})
        ok = c.get("ok", False)
        skipped = c.get("skipped", False)
        status = _fmt(ok, skipped)
        print(f"  [{status:4s}] {code}: {description}")
        if not ok and not skipped:
            detail = (
                c.get("detail")
                or c.get("missing_steps")
                or c.get("missing_scripts")
                or c.get("missing_gates")
                or c.get("missing_scenarios")
                or c.get("failed_scenarios")
            )
            if detail:
                print(f"         → {detail}")
        elif skipped:
            print(f"         → {c.get('reason', 'skipped')}")
        else:
            if key == "test_evidence":
                print(f"         → {c.get('subjects_hashed')}/{c.get('subjects_total')} files hashed, "
                      f"{c.get('scenarios_tested')} scenarios")
            elif key == "scenarios_passed":
                print(f"         → {c.get('scenarios_passed')}/{c.get('scenarios_total')} scenarios passed")
            elif key == "runbook":
                print(f"         → sha256:{c.get('sha256', '')[:16]}... ({c.get('size_bytes')} bytes)")

    print()
    print(f"Checks passed : {result['checks_passed']}/{len(_CHECKS)}")
    print(f"Gate status   : {result['status']}")
    if result.get("fail_reason"):
        print(f"Fail reason   : {result['fail_reason']}")

    print()

    report = {
        "report_type": "AEM_EVOLVE_GATE_EVIDENCE",
        "gate": "ROLLBACK_PROCEDURE_CHECK",
        "pr": "PR11",
        "version": "0.18.0-demo",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "environment": {
            "environment_name": os.getenv("AEM_ENV_NAME", "local-demo"),
            "cloud_provider": os.getenv("AEM_CLOUD_PROVIDER", "N/A"),
            "region": os.getenv("AEM_REGION", "N/A"),
            "deployment_date": os.getenv("AEM_DEPLOYMENT_TIMESTAMP", "N/A"),
            "version_tag": "v2.0.0-pr11",
            "container_image_digest": os.getenv("AEM_CONTAINER_IMAGE_DIGEST", "N/A"),
        },
        "result": result,
        "non_claims": [
            "rollback_tested=false",
            "production_rollback_not_executed",
            "live_database_rollback_not_run",
            "dry_run_only",
        ],
    }

    report_dir = DEMO_ROOT / "assurance" / "evolve-multi-agent" / "v2_0"
    report_dir.mkdir(parents=True, exist_ok=True)
    report_path = report_dir / "rollback_procedure_check_report.json"
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Assurance report → {report_path}")

    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
