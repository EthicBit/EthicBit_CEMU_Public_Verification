#!/usr/bin/env python3
"""Claim boundary checker for MECH-REASON™ — AEM-EVOLVE™ v1.2.

Evaluates an evidence bundle against all R-CLAIM-* policy rules
deterministically. No LLM involvement in rule evaluation.
"""
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]
POLICY_PATH = Path(__file__).parent / "policies/AEM_EVOLVE_POLICY_V1_2.json"
REPORT_OUT = REPO_ROOT / "assurance/evolve-multi-agent/v1_2/claim_boundary_check_report.json"

# Default evidence bundle — reads from v1.1 official status artifact
def _load_evidence_bundle() -> dict:
    official_status = REPO_ROOT / "assurance/evolve-multi-agent/v1_1/OFFICIAL_STATUS_SIGNED.json"
    if official_status.exists():
        with open(official_status) as f:
            return json.load(f)
    return {}

def _load_policy() -> dict:
    with open(POLICY_PATH) as f:
        return json.load(f)

def evaluate_claim_rules(bundle: dict, policy: dict) -> dict:
    results = []
    triggered_fail = []
    policy_version = policy.get("version", "unknown")

    for rule in policy.get("claim_boundary_rules", []):
        rule_id   = rule["rule_id"]
        field     = rule["field"]
        op        = rule["operator"]
        val       = rule["value"]
        outcome   = rule["outcome"]
        severity  = rule["severity"]
        expl      = rule["explanation"]

        actual = bundle.get(field, False)

        if op == "eq":
            triggered = (actual == val)
        else:
            triggered = False

        result = {
            "rule_id": rule_id,
            "field": field,
            "expected_trigger_value": val,
            "actual_value": actual,
            "triggered": triggered,
            "outcome_if_triggered": outcome,
            "severity": severity,
            "explanation": expl,
        }
        results.append(result)
        if triggered:
            triggered_fail.append(rule_id)

    overall = "FAIL_CLOSED" if triggered_fail else "PASS"

    return {
        "schema_id": "AEM_EVOLVE_CLAIM_BOUNDARY_CHECK_REPORT_V1_2",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "policy_version": policy_version,
        "overall_status": overall,
        "triggered_rules": triggered_fail,
        "rules_evaluated": len(results),
        "rule_results": results,
        "claim_boundary_risk_score": round(len(triggered_fail) / max(len(results), 1), 4),
        "llm_involved": False,
        "non_claims": [
            "This check is not regulatory approval.",
            "This check is not legal compliance.",
            "This check is not external certification.",
            "LLM output is not a policy rule.",
            "LLM output does not override this check."
        ]
    }

if __name__ == "__main__":
    policy = _load_policy()
    bundle = _load_evidence_bundle()
    report = evaluate_claim_rules(bundle, policy)

    REPORT_OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(REPORT_OUT, "w") as f:
        json.dump(report, f, indent=2)

    status = report["overall_status"]
    print(f"CLAIM_BOUNDARY_CHECK={status}")
    if status != "PASS":
        for r in report["triggered_rules"]:
            print(f"  TRIGGERED: {r}", file=sys.stderr)
        sys.exit(1)
