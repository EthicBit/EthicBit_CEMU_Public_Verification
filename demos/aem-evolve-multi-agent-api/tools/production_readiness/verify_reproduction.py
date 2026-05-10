#!/usr/bin/env python3
"""
AEM-EVOLVE™ v2.0 PR 8 — External Reproduction Report Evidence Gate Verifier.

Usage:
    python tools/production_readiness/verify_reproduction.py

Set AEM_REPRODUCER_ID and AEM_REPRODUCTION_DATE for full PASS.

Exit code:
    0 = PASS
    1 = FAIL (expected in local/demo — external reproduction not yet executed)
"""
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

DEMO_ROOT = Path(__file__).resolve().parents[2]
if str(DEMO_ROOT) not in sys.path:
    sys.path.insert(0, str(DEMO_ROOT))

from reproduction.reproduction_gate import ReproductionGate

_CHECKS = [
    ("C-01", "report_v2",            "v2.0 reproduction report (REPRODUCTION_REPORT_V2.md) exists"),
    ("C-02", "challenge_doc",        "Reproduction challenge document (REPRODUCTION_CHALLENGE.md) exists"),
    ("C-03", "pr_coverage",          "Report covers all v2.0 PRs 1-7"),
    ("C-04", "outcome_coverage",     "Report covers all 3 governance outcomes (PASS/SCOPE_LIMITED/FAIL_CLOSED)"),
    ("C-05", "evidence_artifact",    "Evidence artifact with SHA256 checksums of 20 gate files"),
    ("C-06", "hitl_coverage",        "Report covers HITL token enforcement and replay mitigation"),
    ("C-07", "chain_coverage",       "Report covers audit chain integrity verification"),
    ("C-08", "artifact_fingerprint", "Evidence artifact SHA256 fingerprint recorded"),
    ("C-09", "reproducer_id",        "External reproducer identity (AEM_REPRODUCER_ID)"),
    ("C-10", "reproduction_date",    "Reproduction date (AEM_REPRODUCTION_DATE)"),
]


def _fmt(ok: bool, skipped: bool = False) -> str:
    if skipped:
        return "SKIP"
    return "PASS" if ok else "FAIL"


def main() -> int:
    gate = ReproductionGate.from_env()
    result = gate.gate_check()
    checks = result["checks"]

    print("=" * 70)
    print("AEM-EVOLVE™ v2.0 PR 8 — External Reproduction Evidence Gate")
    print("=" * 70)
    print(f"Reproducer ID    : {gate._reproducer_id or '(not set)'}")
    print(f"Reproduction date: {gate._reproduction_date or '(not set)'}")
    print(f"Indep. claimed   : {result['independent_reproduction_claimed']}")
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
                or c.get("missing_prs")
                or c.get("missing_outcomes")
                or c.get("missing_terms")
            )
            if detail:
                print(f"         → {detail}")
        elif skipped:
            print(f"         → {c.get('reason', 'skipped')}")
        else:
            if key == "evidence_artifact":
                print(f"         → {c.get('subjects_hashed')}/{c.get('subjects_total')} files hashed, coverage: {c.get('pr_coverage')}")

    print()
    print(f"Checks passed : {result['checks_passed']}/{len(_CHECKS)}")
    print(f"Gate status   : {result['status']}")
    if result.get("fail_reason"):
        print(f"Fail reason   : {result['fail_reason']}")

    print()

    report = {
        "report_type": "AEM_EVOLVE_GATE_EVIDENCE",
        "gate": "EXTERNAL_REPRODUCTION_CHECK",
        "pr": "PR8",
        "version": "0.15.0-demo",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "environment": {
            "environment_name": os.getenv("AEM_ENV_NAME", "local-demo"),
            "cloud_provider": os.getenv("AEM_CLOUD_PROVIDER", "N/A"),
            "region": os.getenv("AEM_REGION", "N/A"),
            "deployment_date": os.getenv("AEM_DEPLOYMENT_DATE", "N/A"),
            "version_tag": "v2.0.0-pr8",
            "container_image_digest": os.getenv("AEM_CONTAINER_IMAGE_DIGEST", "N/A"),
        },
        "result": result,
        "non_claims": [
            "independent_reproduction_not_yet_completed",
            "third_party_attested=false",
            "external_reproducer_identity_not_confirmed",
            "reproduction_steps_not_executed_in_separate_environment",
        ],
    }

    report_dir = DEMO_ROOT / "assurance" / "evolve-multi-agent" / "v2_0"
    report_dir.mkdir(parents=True, exist_ok=True)
    report_path = report_dir / "reproduction_check_report.json"
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Assurance report → {report_path}")

    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
