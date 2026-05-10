#!/usr/bin/env python3
"""
AEM-EVOLVE™ v2.0 PR 9 — Production Deployment Audit Evidence Gate Verifier.

Usage:
    python tools/production_readiness/verify_deployment_audit.py

Set AEM_DEPLOYMENT_TARGET and AEM_DEPLOYMENT_TIMESTAMP for full PASS.

Exit code:
    0 = PASS
    1 = FAIL (expected in local/demo — production deployment not yet executed)
"""
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

DEMO_ROOT = Path(__file__).resolve().parents[2]
if str(DEMO_ROOT) not in sys.path:
    sys.path.insert(0, str(DEMO_ROOT))

from deployment.deployment_gate import DeploymentGate

_CHECKS = [
    ("C-01", "manifest",             "Deployment manifest (DEPLOYMENT_MANIFEST.md) exists"),
    ("C-02", "target_environment",   "Manifest specifies all 6 target environment fields"),
    ("C-03", "env_vars_documented",  "All 14 required env vars documented in manifest"),
    ("C-04", "gate_checklist",       "Pre-deployment checklist covers all 9 gates (PR1-PR9)"),
    ("C-05", "gate_verifiers",       "All 9 gate verifier scripts exist on disk"),
    ("C-06", "rollback_plan",        "Rollback plan documented with DB rollback reference"),
    ("C-07", "health_endpoints",     "Health check endpoints documented (/health, /healthz, /metrics)"),
    ("C-08", "audit_artifact",       "Deployment audit artifact with SHA256 checksums of ≥15 files"),
    ("C-09", "deployment_target",    "Production deployment target (AEM_DEPLOYMENT_TARGET)"),
    ("C-10", "deployment_timestamp", "Production deployment timestamp (AEM_DEPLOYMENT_TIMESTAMP)"),
]


def _fmt(ok: bool, skipped: bool = False) -> str:
    if skipped:
        return "SKIP"
    return "PASS" if ok else "FAIL"


def main() -> int:
    gate = DeploymentGate.from_env()
    result = gate.gate_check()
    checks = result["checks"]

    print("=" * 70)
    print("AEM-EVOLVE™ v2.0 PR 9 — Production Deployment Audit Gate")
    print("=" * 70)
    print(f"Deployment target   : {gate._deployment_target or '(not set)'}")
    print(f"Deployment timestamp: {gate._deployment_timestamp or '(not set)'}")
    print(f"Production deployed : {result['production_deployed']}")
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
                or c.get("missing_env_vars")
                or c.get("missing_gates")
                or c.get("missing_verifiers")
                or c.get("missing_endpoints")
            )
            if detail:
                print(f"         → {detail}")
        elif skipped:
            print(f"         → {c.get('reason', 'skipped')}")
        else:
            if key == "audit_artifact":
                print(f"         → {c.get('subjects_hashed')}/{c.get('subjects_total')} files hashed")
            elif key == "manifest":
                print(f"         → sha256:{c.get('sha256', '')[:16]}... ({c.get('size_bytes')} bytes)")

    print()
    print(f"Checks passed : {result['checks_passed']}/{len(_CHECKS)}")
    print(f"Gate status   : {result['status']}")
    if result.get("fail_reason"):
        print(f"Fail reason   : {result['fail_reason']}")

    print()

    report = {
        "report_type": "AEM_EVOLVE_GATE_EVIDENCE",
        "gate": "PRODUCTION_DEPLOYMENT_AUDIT_CHECK",
        "pr": "PR9",
        "version": "0.16.0-demo",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "environment": {
            "environment_name": os.getenv("AEM_ENV_NAME", "local-demo"),
            "cloud_provider": os.getenv("AEM_CLOUD_PROVIDER", "N/A"),
            "region": os.getenv("AEM_REGION", "N/A"),
            "deployment_date": os.getenv("AEM_DEPLOYMENT_TIMESTAMP", "N/A"),
            "version_tag": "v2.0.0-pr9",
            "container_image_digest": os.getenv("AEM_CONTAINER_IMAGE_DIGEST", "N/A"),
        },
        "result": result,
        "non_claims": [
            "production_deployment_not_yet_executed",
            "deployment_target_not_set",
            "deployment_timestamp_not_set",
            "production_deployed=false",
        ],
    }

    report_dir = DEMO_ROOT / "assurance" / "evolve-multi-agent" / "v2_0"
    report_dir.mkdir(parents=True, exist_ok=True)
    report_path = report_dir / "deployment_audit_check_report.json"
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Assurance report → {report_path}")

    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
