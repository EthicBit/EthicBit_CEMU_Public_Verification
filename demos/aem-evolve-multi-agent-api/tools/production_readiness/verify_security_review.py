#!/usr/bin/env python3
"""
AEM-EVOLVE™ v2.0 PR 7 — Security Review Evidence Gate Verifier.

Usage:
    python tools/production_readiness/verify_security_review.py

Set AEM_SECURITY_REVIEWER and AEM_SECURITY_REVIEW_DATE for full PASS.

Exit code:
    0 = PASS
    1 = FAIL (expected in local/demo — external reviewer not yet engaged)
"""
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

DEMO_ROOT = Path(__file__).resolve().parents[2]
if str(DEMO_ROOT) not in sys.path:
    sys.path.insert(0, str(DEMO_ROOT))

from security_review.security_review_gate import SecurityReviewGate

_CHECKS = [
    ("C-01", "review_document",       "Security review document (SECURITY_REVIEW.md) exists"),
    ("C-02", "threat_model",          "Threat model covers required attack surfaces"),
    ("C-03", "controls_coverage",     "Review covers all 7 governance security controls"),
    ("C-04", "dependency_scan",       "Dependency scan — 0 known CVEs (pip-audit)"),
    ("C-05", "static_analysis",       "Static analysis — 0 HIGH findings (bandit)"),
    ("C-06", "owasp_coverage",        "OWASP API Security Top 10 coverage"),
    ("C-07", "findings_documented",   "Findings documented with dispositions and mitigations"),
    ("C-08", "artifact_fingerprints", "Scan artifact SHA256 fingerprints recorded"),
    ("C-09", "external_reviewer",     "External reviewer identity (AEM_SECURITY_REVIEWER)"),
    ("C-10", "review_date",           "External review date (AEM_SECURITY_REVIEW_DATE)"),
]


def _fmt(ok: bool, skipped: bool = False) -> str:
    if skipped:
        return "SKIP"
    return "PASS" if ok else "FAIL"


def main() -> int:
    gate = SecurityReviewGate.from_env()
    result = gate.gate_check()
    checks = result["checks"]

    print("=" * 70)
    print("AEM-EVOLVE™ v2.0 PR 7 — Security Review Evidence Gate")
    print("=" * 70)
    print(f"External reviewer : {gate._security_reviewer or '(not set)'}")
    print(f"Review date       : {gate._security_review_date or '(not set)'}")
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
                or c.get("missing_threats")
                or c.get("missing_controls")
                or c.get("missing_items")
            )
            if detail:
                print(f"         → {detail}")
            # Extra detail for scan checks
            if key == "dependency_scan" and ok:
                print(f"         → {c.get('dependencies_scanned')} deps, {c.get('vulnerabilities_found')} CVEs")
            if key == "static_analysis" and ok:
                print(f"         → HIGH:{c.get('issues_high')} MED:{c.get('issues_medium')} LOW:{c.get('issues_low')}")
        elif skipped:
            print(f"         → {c.get('reason', 'skipped')}")
        else:
            if key == "dependency_scan":
                print(f"         → {c.get('dependencies_scanned')} deps, {c.get('vulnerabilities_found')} CVEs")
            if key == "static_analysis":
                print(f"         → HIGH:{c.get('issues_high')} MED:{c.get('issues_medium')} LOW:{c.get('issues_low')}")

    print()
    print(f"Checks passed : {result['checks_passed']}/{len(_CHECKS)}")
    print(f"Gate status   : {result['status']}")
    if result.get("fail_reason"):
        print(f"Fail reason   : {result['fail_reason']}")

    print()

    # ── Assurance report ────────────────────────────────────────────────────
    report = {
        "report_type": "AEM_EVOLVE_GATE_EVIDENCE",
        "gate": "SECURITY_REVIEW_CHECK",
        "pr": "PR7",
        "version": "0.14.0-demo",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "environment": {
            "environment_name": os.getenv("AEM_ENV_NAME", "local-demo"),
            "cloud_provider": os.getenv("AEM_CLOUD_PROVIDER", "N/A"),
            "region": os.getenv("AEM_REGION", "N/A"),
            "deployment_date": os.getenv("AEM_DEPLOYMENT_DATE", "N/A"),
            "version_tag": "v2.0.0-pr7",
            "container_image_digest": os.getenv("AEM_CONTAINER_IMAGE_DIGEST", "N/A"),
        },
        "result": result,
        "non_claims": [
            "external_review_not_yet_completed",
            "scan_covers_demo_codebase_not_production_infrastructure",
            "no_penetration_testing_performed",
            "regulatory_approval_not_claimed",
        ],
    }

    report_dir = DEMO_ROOT / "assurance" / "evolve-multi-agent" / "v2_0"
    report_dir.mkdir(parents=True, exist_ok=True)
    report_path = report_dir / "security_review_check_report.json"
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Assurance report → {report_path}")

    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
