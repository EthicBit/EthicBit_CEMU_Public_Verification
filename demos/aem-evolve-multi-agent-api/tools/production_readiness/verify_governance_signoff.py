#!/usr/bin/env python3
"""
AEM-EVOLVE™ v2.0 PR 14 — Governance Sign-Off Gate Verifier.

Usage:
    python tools/production_readiness/verify_governance_signoff.py

Set AEM_GOVERNANCE_APPROVER and AEM_GOVERNANCE_SIGNOFF_DATE for full PASS.

Exit code:
    0 = PASS
    1 = FAIL (expected in local/demo — governance sign-off not configured)
"""
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

DEMO_ROOT = Path(__file__).resolve().parents[2]
if str(DEMO_ROOT) not in sys.path:
    sys.path.insert(0, str(DEMO_ROOT))

from governance_signoff.governance_signoff_gate import GovernanceSignoffGate

_CHECKS = [
    ("C-01", "signoff_document",         "Governance sign-off document present (docs/GOVERNANCE_SIGNOFF.md)"),
    ("C-02", "regulatory_mappings",      "All 3 regulatory mapping documents present (EU AI Act, ISO 42001, NIST AI RMF)"),
    ("C-03", "assurance_reports",        "All 9 v2.0 assurance reports present in assurance/evolve-multi-agent/v2_0/"),
    ("C-04", "pr13_evidence_complete",   "PR13 production readiness report has gates_evidence_complete=True"),
    ("C-05", "claims_document",          "CLAIMS_AND_NON_CLAIMS.md present with required non-claim terms"),
    ("C-06", "signoff_evidence",         "Governance sign-off evidence artifact with SHA256 of ≥15 subjects"),
    ("C-07", "gate_ids_verified",        "All 8 gate IDs verified in PR13 aggregate report"),
    ("C-08", "artifact_fingerprint",     "Evidence artifact SHA256 fingerprint recorded"),
    ("C-09", "governance_approver",      "Governance approver identity (AEM_GOVERNANCE_APPROVER)"),
    ("C-10", "governance_signoff_date",  "Governance sign-off date (AEM_GOVERNANCE_SIGNOFF_DATE)"),
]


def _fmt(ok: bool, skipped: bool = False) -> str:
    if skipped:
        return "SKIP"
    return "PASS" if ok else "FAIL"


def main() -> int:
    gate = GovernanceSignoffGate.from_env()
    result = gate.gate_check()
    checks = result["checks"]

    print("=" * 70)
    print("AEM-EVOLVE™ v2.0 PR 14 — Governance Sign-Off Gate")
    print("=" * 70)
    print(f"Governance approver  : {gate._governance_approver or '(not set)'}")
    print(f"Governance sign-off date: {gate._governance_signoff_date or '(not set)'}")
    print(f"Governance signed off: {result['governance_signed_off']}")
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
                or c.get("missing_regulatory_files")
                or c.get("missing_reports")
                or c.get("missing_terms")
                or c.get("missing_gate_ids")
            )
            if detail:
                print(f"         → {detail}")
        elif skipped:
            print(f"         → {c.get('reason', 'skipped')}")
        else:
            if key == "regulatory_mappings":
                print(f"         → {c.get('regulatory_files_present')}/{c.get('regulatory_files_required')} regulatory mappings present")
            elif key == "assurance_reports":
                print(f"         → {c.get('assurance_reports_present')}/{c.get('assurance_reports_required')} assurance reports present")
            elif key == "signoff_evidence":
                print(f"         → {c.get('subjects_hashed')}/{c.get('subjects_total')} subjects hashed")
            elif key == "gate_ids_verified":
                print(f"         → {c.get('gates_verified')}/{c.get('gates_required')} gate IDs verified")

    print()
    print(f"Checks passed : {result['checks_passed']}/{len(_CHECKS)}")
    print(f"Gate status   : {result['status']}")
    if result.get("fail_reason"):
        print(f"Fail reason   : {result['fail_reason']}")

    print()

    report = {
        "report_type": "AEM_EVOLVE_GATE_EVIDENCE",
        "gate": "GOVERNANCE_SIGNOFF_CHECK",
        "pr": "PR14",
        "version": "0.21.0-demo",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "environment": {
            "environment_name": os.getenv("AEM_ENV_NAME", "local-demo"),
            "cloud_provider": os.getenv("AEM_CLOUD_PROVIDER", "N/A"),
            "region": os.getenv("AEM_REGION", "N/A"),
            "deployment_date": os.getenv("AEM_DEPLOYMENT_TIMESTAMP", "N/A"),
            "version_tag": "v2.0.0-pr14",
            "container_image_digest": os.getenv("AEM_CONTAINER_IMAGE_DIGEST", "N/A"),
        },
        "result": result,
        "non_claims": [
            "governance_signed_off=false",
            "production_ready=false",
            "live_infrastructure_not_validated",
            "regulatory_approval_not_claimed",
            "not_independently_certified",
        ],
    }

    report_dir = DEMO_ROOT / "assurance" / "evolve-multi-agent" / "v2_0"
    report_dir.mkdir(parents=True, exist_ok=True)
    report_path = report_dir / "governance_signoff_check_report.json"
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Assurance report → {report_path}")

    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
