#!/usr/bin/env python3
"""
AEM-EVOLVE™ v2.0 PR 13 — Production Readiness Gate Aggregator Verifier.

Usage:
    python tools/production_readiness/verify_production_readiness.py

Set AEM_READINESS_REVIEWER and AEM_READINESS_REVIEW_DATE for full PASS.

Exit code:
    0 = PASS
    1 = FAIL (expected in local/demo — live infrastructure not configured)
"""
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

DEMO_ROOT = Path(__file__).resolve().parents[2]
if str(DEMO_ROOT) not in sys.path:
    sys.path.insert(0, str(DEMO_ROOT))

from readiness.readiness_gate import ReadinessGate

_CHECKS = [
    ("C-01", "verifiers_present",    "All 12 gate verifier scripts present in tools/production_readiness/"),
    ("C-02", "gate_modules_load",    "All 8 importable gate modules (PR5–PR12) load without error"),
    ("C-03", "pr5_pr6",              "PR5 (Monitoring) + PR6 (Incident Response) — ≥8 file-based checks each"),
    ("C-04", "pr7_pr8",              "PR7 (Security Review) + PR8 (Reproduction) — ≥8 file-based checks each"),
    ("C-05", "pr9_pr10",             "PR9 (Deployment Audit) + PR10 (SLO Evidence) — ≥8 file-based checks each"),
    ("C-06", "pr11_pr12",            "PR11 (Rollback Procedure) + PR12 (Disaster Recovery) — ≥8 file-based checks each"),
    ("C-07", "aggregate_evidence",   "Aggregate readiness evidence artifact with SHA256 of ≥15 gate evidence files"),
    ("C-08", "artifact_fingerprint", "Aggregate evidence artifact SHA256 fingerprint recorded"),
    ("C-09", "readiness_reviewer",   "Production readiness reviewer identity (AEM_READINESS_REVIEWER)"),
    ("C-10", "readiness_review_date","Production readiness review date (AEM_READINESS_REVIEW_DATE)"),
]


def _fmt(ok: bool, skipped: bool = False) -> str:
    if skipped:
        return "SKIP"
    return "PASS" if ok else "FAIL"


def main() -> int:
    gate = ReadinessGate.from_env()
    result = gate.gate_check()
    checks = result["checks"]
    gate_summary = result.get("gate_summary", {})

    print("=" * 70)
    print("AEM-EVOLVE™ v2.0 PR 13 — Production Readiness Gate Aggregator")
    print("=" * 70)
    print(f"Readiness reviewer  : {gate._readiness_reviewer or '(not set)'}")
    print(f"Readiness review date: {gate._readiness_review_date or '(not set)'}")
    print(f"Production ready    : {result['production_ready']}")
    print(f"Gates evidence complete: {result['gates_evidence_complete']}")
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
                or c.get("missing_verifiers")
                or c.get("failed_modules")
            )
            if detail:
                print(f"         → {detail}")
            gates = c.get("gates", {})
            for gname, gdata in gates.items():
                if not gdata.get("ok"):
                    print(f"         → {gname}: {gdata.get('file_checks_passed', '?')}/8 file checks passed")
        elif skipped:
            print(f"         → {c.get('reason', 'skipped')}")
        else:
            if key in ("pr5_pr6", "pr7_pr8", "pr9_pr10", "pr11_pr12"):
                for gname, gdata in c.get("gates", {}).items():
                    print(f"         → {gname}: {gdata.get('file_checks_passed')}/8 file checks pass")
            elif key == "aggregate_evidence":
                print(f"         → {c.get('subjects_hashed')}/{c.get('subjects_total')} files hashed")

    print()
    print("── Gate Summary (all 8 importable gates) ──")
    for class_name, g in gate_summary.items():
        status_str = g.get("status", "ERROR")
        fp = g.get("file_checks_passed", "?")
        total = g.get("checks_passed", "?")
        gate_id = g.get("gate", class_name)
        print(f"  {status_str:4s}  {gate_id}  ({fp}/8 file-based, {total}/10 total)")

    print()
    print(f"Checks passed : {result['checks_passed']}/{len(_CHECKS)}")
    print(f"Gate status   : {result['status']}")
    if result.get("fail_reason"):
        print(f"Fail reason   : {result['fail_reason']}")

    print()

    report = {
        "report_type": "AEM_EVOLVE_GATE_EVIDENCE",
        "gate": "PRODUCTION_READINESS_GATE",
        "pr": "PR13",
        "version": "0.20.0-demo",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "environment": {
            "environment_name": os.getenv("AEM_ENV_NAME", "local-demo"),
            "cloud_provider": os.getenv("AEM_CLOUD_PROVIDER", "N/A"),
            "region": os.getenv("AEM_REGION", "N/A"),
            "deployment_date": os.getenv("AEM_DEPLOYMENT_TIMESTAMP", "N/A"),
            "version_tag": "v2.0.0-pr13",
            "container_image_digest": os.getenv("AEM_CONTAINER_IMAGE_DIGEST", "N/A"),
        },
        "result": result,
        "non_claims": [
            "production_ready=false",
            "live_infrastructure_not_validated",
            "independent_reproduction_not_claimed",
            "regulatory_approval_not_claimed",
            "not_tamper_proof",
        ],
    }

    report_dir = DEMO_ROOT / "assurance" / "evolve-multi-agent" / "v2_0"
    report_dir.mkdir(parents=True, exist_ok=True)
    report_path = report_dir / "production_readiness_gate_report.json"
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Assurance report → {report_path}")

    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
