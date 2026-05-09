#!/usr/bin/env python3
"""Governance risk scorer for MECH-REASON™ — AEM-EVOLVE™ v1.2.

Computes governance risk, claim boundary risk, HITL necessity score,
anchor integrity score, receipt integrity score, and regulatory mapping
presence score deterministically. No LLM involvement.
"""
import json
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]
V1_1 = REPO_ROOT / "assurance/evolve-multi-agent/v1_1"
EXEC = REPO_ROOT / "assurance/evolve-multi-agent/execution"
REPORT_OUT = REPO_ROOT / "assurance/evolve-multi-agent/v1_2/governance_risk_score_report.json"

def _load(path: Path) -> dict:
    if not path.exists():
        return {}
    with open(path) as f:
        return json.load(f)

def score_anchor_integrity() -> float:
    anchor = _load(REPO_ROOT / "assurance/evolve-multi-agent/AEM_EVOLVE_MULTI_AGENT_API_ANCHOR_RECEIPT.json")
    multi  = _load(V1_1 / "multi_anchor_verification_report.json")
    score  = 0.0
    if anchor.get("network") == "ethereum-mainnet":
        score += 0.50
    if multi.get("ethereum_mainnet_anchor") == "PASS":
        score += 0.25
    if multi.get("triple_public_anchor") == "PASS":
        score += 0.25
    return round(score, 4)

def score_receipt_integrity() -> float:
    forgery = _load(V1_1 / "receipt_forgery_test_report.json")
    rate    = forgery.get("tamper_detected_rate", 0.0)
    tests   = forgery.get("tests_run", 0)
    if tests == 0:
        return 0.0
    return round(rate, 4)

def score_regulatory_mapping_presence() -> float:
    reg = _load(V1_1 / "regulatory_mapping_check_report.json")
    if reg.get("regulatory_mapping_check") == "PASS":
        frameworks = reg.get("frameworks_checked", [])
        return round(min(len(frameworks) / 3.0, 1.0), 4)
    return 0.0

def score_hitl_necessity() -> float:
    hitl = _load(V1_1 / "hitl_signature_verification_report.json")
    decisions = _load(EXEC / "HUMAN_DECISIONS.json")
    score = 0.0
    if hitl.get("approver_role_verified"):
        score += 0.50
    if hitl.get("decision_hash_verified"):
        score += 0.25
    count = decisions.get("decisions_count", 0)
    if count > 0:
        score += 0.25
    return round(score, 4)

def score_claim_boundary_risk() -> float:
    cb = _load(REPO_ROOT / "assurance/evolve-multi-agent/v1_2/claim_boundary_check_report.json")
    return round(cb.get("claim_boundary_risk_score", 0.0), 4)

def score_governance_risk(
    anchor: float,
    receipt: float,
    reg_map: float,
    hitl: float,
    claim_risk: float,
    completeness: float,
) -> float:
    # Higher sub-scores = lower risk → invert for risk
    risk = (
        (1.0 - anchor)    * 0.20 +
        (1.0 - receipt)   * 0.25 +
        (1.0 - reg_map)   * 0.15 +
        (1.0 - hitl)      * 0.15 +
        claim_risk        * 0.15 +
        (1.0 - completeness) * 0.10
    )
    return round(min(max(risk, 0.0), 1.0), 4)

if __name__ == "__main__":
    # Load completeness score from its report if already generated
    comp_report = _load(REPO_ROOT / "assurance/evolve-multi-agent/v1_2/evidence_completeness_report.json")
    completeness = comp_report.get("evidence_completeness_score", 0.5)

    anchor_score  = score_anchor_integrity()
    receipt_score = score_receipt_integrity()
    reg_score     = score_regulatory_mapping_presence()
    hitl_score    = score_hitl_necessity()
    claim_risk    = score_claim_boundary_risk()
    gov_risk      = score_governance_risk(anchor_score, receipt_score, reg_score,
                                          hitl_score, claim_risk, completeness)

    if gov_risk <= 0.40:
        status = "PASS"
    elif gov_risk <= 0.70:
        status = "SCOPE_LIMITED"
    else:
        status = "FAIL_CLOSED"

    report = {
        "schema_id": "AEM_EVOLVE_GOVERNANCE_RISK_SCORE_REPORT_V1_2",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "governance_risk_score": gov_risk,
        "claim_boundary_risk_score": claim_risk,
        "hitl_necessity_score": hitl_score,
        "anchor_integrity_score": anchor_score,
        "receipt_integrity_score": receipt_score,
        "regulatory_mapping_presence_score": reg_score,
        "evidence_completeness_score_input": completeness,
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

    print(f"GOVERNANCE_RISK_SCORE={status}")
