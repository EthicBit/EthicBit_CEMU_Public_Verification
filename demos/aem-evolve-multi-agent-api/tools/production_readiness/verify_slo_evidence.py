#!/usr/bin/env python3
"""
AEM-EVOLVE™ v2.0 PR 10 — SLO Evidence Gate Verifier.

Usage:
    python tools/production_readiness/verify_slo_evidence.py

Set AEM_SLO_REVIEWER and AEM_SLO_REVIEW_DATE for full PASS.

Exit code:
    0 = PASS
    1 = FAIL (expected in local/demo — SLO review not yet executed)
"""
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

DEMO_ROOT = Path(__file__).resolve().parents[2]
if str(DEMO_ROOT) not in sys.path:
    sys.path.insert(0, str(DEMO_ROOT))

from slo.slo_gate import SLOGate

_CHECKS = [
    ("C-01", "slo_document",              "SLO document (SLO.md) exists"),
    ("C-02", "slo_targets",               "SLO targets cover all 4 dimensions (availability, latency_p99, error_rate, governance)"),
    ("C-03", "error_budgets",             "Error budget calculations documented with burn rate thresholds"),
    ("C-04", "burn_rate_alerts",          "Burn rate alert rules documented (fast_burn + slow_burn)"),
    ("C-05", "measurement_methodology",   "SLO measurement methodology documented with counter-to-SLO mapping"),
    ("C-06", "governance_gate_coverage",  "Governance gate SLO coverage for all 9 gates (PR1-PR9)"),
    ("C-07", "slo_evidence_artifact",     "SLO evidence artifact with SHA256 checksums of ≥15 gate evidence files"),
    ("C-08", "artifact_fingerprint",      "SLO evidence artifact SHA256 fingerprint recorded"),
    ("C-09", "slo_reviewer",              "External SLO reviewer identity (AEM_SLO_REVIEWER)"),
    ("C-10", "slo_review_date",           "SLO review date (AEM_SLO_REVIEW_DATE)"),
]


def _fmt(ok: bool, skipped: bool = False) -> str:
    if skipped:
        return "SKIP"
    return "PASS" if ok else "FAIL"


def main() -> int:
    gate = SLOGate.from_env()
    result = gate.gate_check()
    checks = result["checks"]

    print("=" * 70)
    print("AEM-EVOLVE™ v2.0 PR 10 — SLO Evidence Gate")
    print("=" * 70)
    print(f"SLO reviewer  : {gate._slo_reviewer or '(not set)'}")
    print(f"SLO review date: {gate._slo_review_date or '(not set)'}")
    print(f"Evidence verified: {result['slo_evidence_verified']}")
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
                or c.get("missing_dimensions")
                or c.get("missing_fields")
                or c.get("missing_terms")
                or c.get("missing_gates")
            )
            if detail:
                print(f"         → {detail}")
        elif skipped:
            print(f"         → {c.get('reason', 'skipped')}")
        else:
            if key == "slo_evidence_artifact":
                print(f"         → {c.get('subjects_hashed')}/{c.get('subjects_total')} files hashed, coverage: {c.get('gate_coverage')}")
            elif key == "slo_document":
                print(f"         → sha256:{c.get('sha256', '')[:16]}... ({c.get('size_bytes')} bytes)")

    print()
    print(f"Checks passed : {result['checks_passed']}/{len(_CHECKS)}")
    print(f"Gate status   : {result['status']}")
    if result.get("fail_reason"):
        print(f"Fail reason   : {result['fail_reason']}")

    print()

    report = {
        "report_type": "AEM_EVOLVE_GATE_EVIDENCE",
        "gate": "SLO_EVIDENCE_CHECK",
        "pr": "PR10",
        "version": "0.17.0-demo",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "environment": {
            "environment_name": os.getenv("AEM_ENV_NAME", "local-demo"),
            "cloud_provider": os.getenv("AEM_CLOUD_PROVIDER", "N/A"),
            "region": os.getenv("AEM_REGION", "N/A"),
            "deployment_date": os.getenv("AEM_DEPLOYMENT_TIMESTAMP", "N/A"),
            "version_tag": "v2.0.0-pr10",
            "container_image_digest": os.getenv("AEM_CONTAINER_IMAGE_DIGEST", "N/A"),
        },
        "result": result,
        "non_claims": [
            "slo_evidence_verified=false",
            "live_slo_measurement_not_running",
            "production_prometheus_not_connected",
            "error_budget_not_tracked_in_production",
        ],
    }

    report_dir = DEMO_ROOT / "assurance" / "evolve-multi-agent" / "v2_0"
    report_dir.mkdir(parents=True, exist_ok=True)
    report_path = report_dir / "slo_evidence_check_report.json"
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Assurance report → {report_path}")

    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
