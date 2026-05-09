#!/usr/bin/env python3
"""Regulatory mapping checker for AEM-EVOLVE™ v1.1.

Verifies that regulatory mapping JSON files comply with the non-approval
boundary: correct schema, mapping_type, and all approval flags set to false.
"""
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]
MAPPING_DIR = REPO_ROOT / "demos/aem-evolve-multi-agent-api/docs/regulatory"
REPORT_OUT = REPO_ROOT / "assurance/evolve-multi-agent/v1_1/regulatory_mapping_check_report.json"

REQUIRED_FRAMEWORKS = ["EU_AI_ACT", "NIST_AI_RMF", "ISO_42001"]
FRAMEWORK_FILES = {
    "EU_AI_ACT":    MAPPING_DIR / "EU_AI_ACT_MAPPING.json",
    "NIST_AI_RMF":  MAPPING_DIR / "NIST_AI_RMF_MAPPING.json",
    "ISO_42001":    MAPPING_DIR / "ISO_42001_MAPPING.json",
}

REQUIRED_SCHEMA_ID = "AEM_EVOLVE_REGULATORY_MAPPING_V1_1"
REQUIRED_MAPPING_TYPE = "technical_mapping_non_approval"
FORBIDDEN_CLAIM_TEXT = "compliance evidence"

errors = []
framework_results = {}

def check_mapping(framework: str, path: Path) -> dict:
    result = {"framework": framework, "status": "PASS", "issues": []}

    if not path.exists():
        result["status"] = "FAIL"
        result["issues"].append(f"File not found: {path}")
        return result

    with open(path) as f:
        data = json.load(f)

    if data.get("schema_id") != REQUIRED_SCHEMA_ID:
        result["issues"].append(f"schema_id mismatch: {data.get('schema_id')!r}")

    if data.get("mapping_type") != REQUIRED_MAPPING_TYPE:
        result["issues"].append(f"mapping_type must be {REQUIRED_MAPPING_TYPE!r}")

    for flag in ("approval_claimed", "certification_claimed",
                 "legal_compliance_claimed", "conformity_assessment_claimed"):
        if data.get(flag) is not False:
            result["issues"].append(f"{flag} must be false")

    if not data.get("mapped_capabilities"):
        result["issues"].append("mapped_capabilities is empty or missing")

    non_claims = data.get("non_claims", [])
    if not non_claims:
        result["issues"].append("non_claims is empty or missing")

    full_text = json.dumps(data).lower()
    if FORBIDDEN_CLAIM_TEXT in full_text:
        result["issues"].append(f"Forbidden text found: {FORBIDDEN_CLAIM_TEXT!r}")

    if result["issues"]:
        result["status"] = "FAIL"

    return result

for framework in REQUIRED_FRAMEWORKS:
    res = check_mapping(framework, FRAMEWORK_FILES[framework])
    framework_results[framework] = res
    if res["status"] != "PASS":
        errors.extend(res["issues"])

overall = "PASS" if not errors else "FAIL"

report = {
    "schema_id": "AEM_EVOLVE_REGULATORY_MAPPING_CHECK_REPORT_V1_1",
    "generated_at": datetime.now(timezone.utc).isoformat(),
    "status": overall,
    "frameworks_checked": REQUIRED_FRAMEWORKS,
    "regulatory_mapping_check": overall,
    "approval_claimed": False,
    "certification_claimed": False,
    "legal_compliance_claimed": False,
    "conformity_assessment_claimed": False,
    "non_approval_boundary_confirmed": overall == "PASS",
    "framework_results": framework_results,
    "errors": errors,
    "non_claims": [
        "This report is not regulatory approval.",
        "This report is not legal compliance.",
        "This report is not conformity assessment.",
        "This report is not external certification."
    ]
}

REPORT_OUT.parent.mkdir(parents=True, exist_ok=True)
with open(REPORT_OUT, "w") as f:
    json.dump(report, f, indent=2)

print(f"REGULATORY_MAPPING_CHECK={overall}")
if errors:
    for e in errors:
        print(f"  ERROR: {e}", file=sys.stderr)
    sys.exit(1)
