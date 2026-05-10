#!/usr/bin/env python3
"""
AEM-EVOLVE™ v2.0 PR 6 — Incident Response Runbook and Drill Evidence Gate Verifier.

Usage:
    python tools/production_readiness/verify_incident_response.py

Set AEM_DRILL_COMPLETED_AT and AEM_DRILL_SIGNOFF_APPROVER for full PASS.

Exit code:
    0 = PASS
    1 = FAIL (expected in local/demo — drill not executed with live sign-off)
"""
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

DEMO_ROOT = Path(__file__).resolve().parents[2]
if str(DEMO_ROOT) not in sys.path:
    sys.path.insert(0, str(DEMO_ROOT))

from incident_response.incident_response_gate import IncidentResponseGate

_CHECKS = [
    ("C-01", "runbook_exists",          "Incident response runbook file exists"),
    ("C-02", "runbook_coverage",        "Runbook covers all 7 mandatory incident types"),
    ("C-03", "severity_levels",         "Severity classification (P1/P2/P3) defined"),
    ("C-04", "escalation_matrix",       "Escalation matrix with named roles"),
    ("C-05", "recovery_procedures",     "Recovery procedures and post-mortem template"),
    ("C-06", "alert_cross_reference",   "All 7 PR 5 alert names cross-referenced"),
    ("C-07", "drill_script",            "Tabletop drill scenario script exists"),
    ("C-08", "drill_evidence",          "Drill evidence artifact with all 7 scenarios"),
    ("C-09", "drill_completed",         "Live drill completion timestamp (AEM_DRILL_COMPLETED_AT)"),
    ("C-10", "drill_signoff",           "Drill sign-off approver (AEM_DRILL_SIGNOFF_APPROVER)"),
]


def _fmt(ok: bool, skipped: bool = False) -> str:
    if skipped:
        return "SKIP"
    return "PASS" if ok else "FAIL"


def main() -> int:
    gate = IncidentResponseGate.from_env()
    result = gate.gate_check()
    checks = result["checks"]

    print("=" * 70)
    print("AEM-EVOLVE™ v2.0 PR 6 — Incident Response Evidence Gate")
    print("=" * 70)
    print(f"Drill completed  : {gate._drill_completed_at or '(not set)'}")
    print(f"Drill sign-off   : {gate._drill_signoff_approver or '(not set)'}")
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
                or c.get("missing_incidents")
                or c.get("missing_severity_levels")
                or c.get("missing_roles")
                or c.get("missing_alerts")
            )
            if detail:
                print(f"         → {detail}")
        elif skipped:
            print(f"         → {c.get('reason', 'skipped')}")

    print()
    print(f"Checks passed : {result['checks_passed']}/{len(_CHECKS)}")
    print(f"Gate status   : {result['status']}")
    if result.get("fail_reason"):
        print(f"Fail reason   : {result['fail_reason']}")

    print()

    # ── Assurance report ────────────────────────────────────────────────────
    report = {
        "report_type": "AEM_EVOLVE_GATE_EVIDENCE",
        "gate": "INCIDENT_RESPONSE_CHECK",
        "pr": "PR6",
        "version": "0.13.0-demo",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "environment": {
            "environment_name": os.getenv("AEM_ENV_NAME", "local-demo"),
            "cloud_provider": os.getenv("AEM_CLOUD_PROVIDER", "N/A"),
            "region": os.getenv("AEM_REGION", "N/A"),
            "deployment_date": os.getenv("AEM_DEPLOYMENT_DATE", "N/A"),
            "version_tag": "v2.0.0-pr6",
            "container_image_digest": os.getenv("AEM_CONTAINER_IMAGE_DIGEST", "N/A"),
        },
        "result": result,
        "non_claims": [
            "drill_not_executed_against_live_environment",
            "alert_delivery_not_verified",
            "sign_off_requires_AEM_DRILL_SIGNOFF_APPROVER",
            "post_mortem_not_yet_completed",
        ],
    }

    report_dir = DEMO_ROOT / "assurance" / "evolve-multi-agent" / "v2_0"
    report_dir.mkdir(parents=True, exist_ok=True)
    report_path = report_dir / "incident_response_check_report.json"
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Assurance report → {report_path}")

    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
