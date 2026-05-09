#!/usr/bin/env python3
"""Evidence completeness scorer for MECH-REASON™ — AEM-EVOLVE™ v1.2.

Scores the completeness of the evidence bundle mechanically.
Each required artifact is checked for existence and basic validity.
No LLM involvement.
"""
import json
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]
REPORT_OUT = REPO_ROOT / "assurance/evolve-multi-agent/v1_2/evidence_completeness_report.json"

# Required evidence artifacts with weight (sum = 1.0)
REQUIRED_ARTIFACTS = [
    {
        "key": "regulatory_mapping",
        "path": "assurance/evolve-multi-agent/v1_1/regulatory_mapping_check_report.json",
        "required_field": "regulatory_mapping_check",
        "required_value": "PASS",
        "weight": 0.15,
    },
    {
        "key": "governance_effectiveness",
        "path": "assurance/evolve-multi-agent/v1_1/governance_effectiveness_report.json",
        "required_field": "status",
        "required_value": "PASS",
        "weight": 0.15,
    },
    {
        "key": "multi_anchor",
        "path": "assurance/evolve-multi-agent/v1_1/multi_anchor_verification_report.json",
        "required_field": "status",
        "required_value": "PASS",
        "weight": 0.15,
    },
    {
        "key": "hitl_verification",
        "path": "assurance/evolve-multi-agent/v1_1/hitl_signature_verification_report.json",
        "required_field": "status",
        "required_value": "PASS_DEMO",
        "weight": 0.15,
    },
    {
        "key": "receipt_forgery",
        "path": "assurance/evolve-multi-agent/v1_1/receipt_forgery_test_report.json",
        "required_field": "status",
        "required_value": "PASS",
        "weight": 0.15,
    },
    {
        "key": "official_status",
        "path": "assurance/evolve-multi-agent/v1_1/OFFICIAL_STATUS_SIGNED.json",
        "required_field": "official_status",
        "required_value": "V1_1_CONTROLLED_ENVIRONMENT_ASSURANCE_UPDATE",
        "weight": 0.10,
    },
    {
        "key": "anchor_receipt",
        "path": "assurance/evolve-multi-agent/AEM_EVOLVE_MULTI_AGENT_API_ANCHOR_RECEIPT.json",
        "required_field": "network",
        "required_value": "ethereum-mainnet",
        "weight": 0.10,
    },
    {
        "key": "human_decisions",
        "path": "assurance/evolve-multi-agent/execution/HUMAN_DECISIONS.json",
        "required_field": "decisions_count",
        "required_value": None,  # just needs to exist with decisions_count > 0
        "weight": 0.05,
    },
]

def score_artifact(artifact: dict) -> dict:
    path = REPO_ROOT / artifact["path"]
    if not path.exists():
        return {"key": artifact["key"], "present": False, "valid": False,
                "score": 0.0, "weight": artifact["weight"], "reason": "file not found"}

    try:
        with open(path) as f:
            data = json.load(f)
    except Exception as e:
        return {"key": artifact["key"], "present": True, "valid": False,
                "score": 0.0, "weight": artifact["weight"], "reason": f"json error: {e}"}

    field = artifact["required_field"]
    expected = artifact["required_value"]

    if field not in data:
        return {"key": artifact["key"], "present": True, "valid": False,
                "score": 0.5, "weight": artifact["weight"], "reason": f"field '{field}' missing"}

    actual = data[field]
    if expected is None:
        # just needs to be truthy
        valid = bool(actual)
    else:
        valid = (actual == expected)

    return {
        "key": artifact["key"],
        "present": True,
        "valid": valid,
        "actual_value": actual,
        "expected_value": expected,
        "score": 1.0 if valid else 0.5,
        "weight": artifact["weight"],
        "reason": "ok" if valid else f"expected {expected!r}, got {actual!r}",
    }

if __name__ == "__main__":
    results = [score_artifact(a) for a in REQUIRED_ARTIFACTS]

    weighted_score = sum(r["score"] * r["weight"] for r in results)
    present_count = sum(1 for r in results if r["present"])
    valid_count = sum(1 for r in results if r["valid"])

    if weighted_score >= 0.80:
        status = "PASS"
    elif weighted_score >= 0.50:
        status = "SCOPE_LIMITED"
    else:
        status = "FAIL_CLOSED"

    report = {
        "schema_id": "AEM_EVOLVE_EVIDENCE_COMPLETENESS_REPORT_V1_2",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "evidence_completeness_score": round(weighted_score, 4),
        "artifacts_checked": len(results),
        "artifacts_present": present_count,
        "artifacts_valid": valid_count,
        "artifact_results": results,
        "llm_involved": False,
        "non_claims": [
            "This score is not regulatory proof.",
            "This score is not production SLA.",
            "LLM output did not contribute to this score."
        ]
    }

    REPORT_OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(REPORT_OUT, "w") as f:
        json.dump(report, f, indent=2)

    print(f"EVIDENCE_COMPLETENESS_SCORE={status}")
