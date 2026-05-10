#!/usr/bin/env python3
"""
AEM-EVOLVE™ v2.0 PR 12 — Disaster Recovery Evidence Gate Verifier.

Usage:
    python tools/production_readiness/verify_disaster_recovery.py

Set AEM_DR_TESTER and AEM_DR_TEST_DATE for full PASS.

Exit code:
    0 = PASS
    1 = FAIL (expected in local/demo — DR dry-run not yet executed with tester identity)
"""
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

DEMO_ROOT = Path(__file__).resolve().parents[2]
if str(DEMO_ROOT) not in sys.path:
    sys.path.insert(0, str(DEMO_ROOT))

from disaster_recovery.disaster_recovery_gate import DisasterRecoveryGate

_CHECKS = [
    ("C-01", "dr_plan",             "DR plan document (DISASTER_RECOVERY.md) exists"),
    ("C-02", "rto_rpo",             "RTO/RPO targets defined (rto_minutes=240, rpo_minutes=60)"),
    ("C-03", "backup_strategy",     "Backup strategy documented (frequency, retention, scope)"),
    ("C-04", "dr_scenarios",        "All 5 DR scenarios documented in test evidence artifact"),
    ("C-05", "recovery_procedures", "Recovery procedures documented for all scenario types"),
    ("C-06", "dr_evidence",         "DR test evidence artifact with SHA256 and ≥5 scenarios"),
    ("C-07", "scenarios_passed",    "All 5 DR dry-run scenarios passed"),
    ("C-08", "artifact_fingerprint","DR test evidence artifact SHA256 fingerprint recorded"),
    ("C-09", "dr_tester",           "DR dry-run tester identity (AEM_DR_TESTER)"),
    ("C-10", "dr_test_date",        "DR dry-run test date (AEM_DR_TEST_DATE)"),
]


def _fmt(ok: bool, skipped: bool = False) -> str:
    if skipped:
        return "SKIP"
    return "PASS" if ok else "FAIL"


def main() -> int:
    gate = DisasterRecoveryGate.from_env()
    result = gate.gate_check()
    checks = result["checks"]

    print("=" * 70)
    print("AEM-EVOLVE™ v2.0 PR 12 — Disaster Recovery Gate")
    print("=" * 70)
    print(f"DR tester   : {gate._dr_tester or '(not set)'}")
    print(f"DR test date: {gate._dr_test_date or '(not set)'}")
    print(f"DR tested   : {result['dr_tested']}")
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
                or c.get("missing_fields")
                or c.get("missing_scenarios")
                or c.get("missing_terms")
                or c.get("failed_scenarios")
            )
            if detail:
                print(f"         → {detail}")
        elif skipped:
            print(f"         → {c.get('reason', 'skipped')}")
        else:
            if key == "dr_evidence":
                print(f"         → {c.get('subjects_hashed')}/{c.get('subjects_total')} files hashed, "
                      f"RTO={c.get('rto_target_minutes')}min, RPO={c.get('rpo_target_minutes')}min")
            elif key == "scenarios_passed":
                print(f"         → {c.get('scenarios_passed')}/{c.get('scenarios_total')} scenarios passed")
            elif key == "dr_plan":
                print(f"         → sha256:{c.get('sha256', '')[:16]}... ({c.get('size_bytes')} bytes)")

    print()
    print(f"Checks passed : {result['checks_passed']}/{len(_CHECKS)}")
    print(f"Gate status   : {result['status']}")
    if result.get("fail_reason"):
        print(f"Fail reason   : {result['fail_reason']}")

    print()

    report = {
        "report_type": "AEM_EVOLVE_GATE_EVIDENCE",
        "gate": "DISASTER_RECOVERY_CHECK",
        "pr": "PR12",
        "version": "0.19.0-demo",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "environment": {
            "environment_name": os.getenv("AEM_ENV_NAME", "local-demo"),
            "cloud_provider": os.getenv("AEM_CLOUD_PROVIDER", "N/A"),
            "region": os.getenv("AEM_REGION", "N/A"),
            "deployment_date": os.getenv("AEM_DEPLOYMENT_TIMESTAMP", "N/A"),
            "version_tag": "v2.0.0-pr12",
            "container_image_digest": os.getenv("AEM_CONTAINER_IMAGE_DIGEST", "N/A"),
        },
        "result": result,
        "non_claims": [
            "dr_tested=false",
            "production_dr_exercise_not_executed",
            "live_database_restore_not_run",
            "region_failover_not_executed",
            "dry_run_only",
        ],
    }

    report_dir = DEMO_ROOT / "assurance" / "evolve-multi-agent" / "v2_0"
    report_dir.mkdir(parents=True, exist_ok=True)
    report_path = report_dir / "disaster_recovery_check_report.json"
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Assurance report → {report_path}")

    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
