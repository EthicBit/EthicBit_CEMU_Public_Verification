#!/usr/bin/env python3
"""MECH-REASON™ deterministic reasoning engine — AEM-EVOLVE™ v1.2.

Orchestrates all sub-components:
  1. Runs claim_boundary_checker
  2. Runs evidence_completeness_scorer
  3. Runs governance_risk_scorer
  4. Applies policy decision table
  5. Applies state machine validation
  6. Infers HITL requirement
  7. Generates mechanical explanation
  8. Seals MECH_REASON_REPORT with input hashes

MECH-REASON recommends mechanically.
MechanicalGate decides deterministically.
ReceiptSealer seals.
LLM output is not final governance.
"""
import hashlib
import importlib.util
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]
V1_2 = REPO_ROOT / "assurance/evolve-multi-agent/v1_2"
TOOLS = Path(__file__).parent
POLICY_PATH = TOOLS / "policies/AEM_EVOLVE_POLICY_V1_2.json"
REPORT_OUT = V1_2 / "MECH_REASON_REPORT.json"

ALLOWED_OUTCOMES = {"PASS", "SCOPE_LIMITED", "FAIL_CLOSED", "ESCALATE_TO_HITL"}
DECISION_PRIORITY = ["FAIL_CLOSED", "ESCALATE_TO_HITL", "SCOPE_LIMITED", "PASS"]


def _sha256_file(path: Path) -> str:
    if not path.exists():
        return ""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load(path: Path) -> dict:
    if not path.exists():
        return {}
    with open(path) as f:
        return json.load(f)


def _run_component(script: Path) -> None:
    result = subprocess.run([sys.executable, str(script)], capture_output=True, text=True)
    if result.returncode != 0:
        print(f"  WARNING: {script.name} exited non-zero: {result.stderr.strip()}", file=sys.stderr)


def _load_policy() -> dict:
    with open(POLICY_PATH) as f:
        return json.load(f)


def _apply_decision_table(
    claim_report: dict,
    completeness_report: dict,
    risk_report: dict,
    policy: dict,
) -> tuple[str, list[str]]:
    triggered: list[str] = []
    candidate_outcomes: list[str] = []

    # Claim boundary failures → FAIL_CLOSED
    for rule_result in claim_report.get("rule_results", []):
        if rule_result.get("triggered"):
            triggered.append(rule_result["rule_id"])
            candidate_outcomes.append("FAIL_CLOSED")

    ev_score = completeness_report.get("evidence_completeness_score", 0.5)
    gr_score = risk_report.get("governance_risk_score", 0.5)
    cb_risk  = risk_report.get("claim_boundary_risk_score", 0.0)

    # HITL rules from policy
    for rule in policy.get("hitl_rules", []):
        rule_id = rule["rule_id"]
        cond    = rule["condition"]
        if "governance_risk_score > 0.70" in cond and gr_score > 0.70:
            triggered.append(rule_id)
            candidate_outcomes.append("ESCALATE_TO_HITL")
        elif "evidence_completeness_score < 0.50" in cond and ev_score < 0.50:
            triggered.append(rule_id)
            candidate_outcomes.append("ESCALATE_TO_HITL")
        elif "claim_boundary_risk_score > 0.60" in cond and cb_risk > 0.60:
            triggered.append(rule_id)
            candidate_outcomes.append("ESCALATE_TO_HITL")

    # Scope rules from policy
    for rule in policy.get("scope_rules", []):
        rule_id = rule["rule_id"]
        cond    = rule["condition"]
        if "evidence_completeness_score >= 0.50" in cond and 0.50 <= ev_score < 0.80:
            triggered.append(rule_id)
            candidate_outcomes.append("SCOPE_LIMITED")
        elif "governance_risk_score >= 0.40" in cond and 0.40 <= gr_score <= 0.70:
            triggered.append(rule_id)
            candidate_outcomes.append("SCOPE_LIMITED")

    if not candidate_outcomes:
        candidate_outcomes.append("PASS")

    # Apply decision priority
    for outcome in DECISION_PRIORITY:
        if outcome in candidate_outcomes:
            return outcome, list(dict.fromkeys(triggered))

    return "PASS", []


def _validate_state_machine(outcome: str, scores: dict) -> dict:
    """Validates that the recommended outcome is reachable from current state."""
    ev = scores.get("evidence_completeness_score", 0.0)
    gr = scores.get("governance_risk_score", 0.0)

    valid_transitions = {
        "PASS":              ev >= 0.80 and gr <= 0.40,
        "SCOPE_LIMITED":     ev >= 0.50 or (0.40 <= gr <= 0.70),
        "FAIL_CLOSED":       True,  # always reachable via claim violation
        "ESCALATE_TO_HITL":  gr > 0.70 or ev < 0.50,
    }
    reachable = valid_transitions.get(outcome, False)
    return {
        "outcome": outcome,
        "state_transition_valid": reachable,
        "reason": "ok" if reachable else f"state machine: {outcome} not reachable from current scores",
    }


def _infer_hitl_required(outcome: str, risk_report: dict, claim_report: dict) -> bool:
    if outcome == "ESCALATE_TO_HITL":
        return True
    if outcome == "FAIL_CLOSED":
        return False
    gr = risk_report.get("governance_risk_score", 0.0)
    hitl_score = risk_report.get("hitl_necessity_score", 0.0)
    return gr > 0.50 or hitl_score >= 0.75


if __name__ == "__main__":
    print("[MECH-REASON™] Running sub-components...")
    _run_component(TOOLS / "claim_boundary_checker.py")
    _run_component(TOOLS / "evidence_completeness_scorer.py")
    _run_component(TOOLS / "governance_risk_scorer.py")

    policy           = _load_policy()
    claim_report     = _load(V1_2 / "claim_boundary_check_report.json")
    comp_report      = _load(V1_2 / "evidence_completeness_report.json")
    risk_report      = _load(V1_2 / "governance_risk_score_report.json")

    scores = {
        "evidence_completeness_score":      comp_report.get("evidence_completeness_score", 0.0),
        "governance_risk_score":            risk_report.get("governance_risk_score", 0.0),
        "claim_boundary_risk_score":        risk_report.get("claim_boundary_risk_score", 0.0),
        "hitl_necessity_score":             risk_report.get("hitl_necessity_score", 0.0),
        "anchor_integrity_score":           risk_report.get("anchor_integrity_score", 0.0),
        "receipt_integrity_score":          risk_report.get("receipt_integrity_score", 0.0),
        "regulatory_mapping_presence_score": risk_report.get("regulatory_mapping_presence_score", 0.0),
    }

    recommended_outcome, triggered_rules = _apply_decision_table(
        claim_report, comp_report, risk_report, policy
    )
    state_validation = _validate_state_machine(recommended_outcome, scores)
    hitl_required    = _infer_hitl_required(recommended_outcome, risk_report, claim_report)

    # Mechanical explanation — import directly
    spec = importlib.util.spec_from_file_location(
        "mechanical_explanation", TOOLS / "mechanical_explanation.py"
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    all_policy_rules = (
        policy.get("claim_boundary_rules", []) +
        policy.get("hitl_rules", []) +
        policy.get("scope_rules", [])
    )
    explanation = mod.generate_explanation(triggered_rules, recommended_outcome, scores, all_policy_rules)

    input_hashes = {
        "claim_boundary_check_report.json":   _sha256_file(V1_2 / "claim_boundary_check_report.json"),
        "evidence_completeness_report.json":  _sha256_file(V1_2 / "evidence_completeness_report.json"),
        "governance_risk_score_report.json":  _sha256_file(V1_2 / "governance_risk_score_report.json"),
        "AEM_EVOLVE_POLICY_V1_2.json":        _sha256_file(POLICY_PATH),
    }
    report_hash = hashlib.sha256(
        json.dumps({
            "recommended_outcome": recommended_outcome,
            "triggered_rules": triggered_rules,
            "scores": scores,
            "input_hashes": input_hashes,
        }, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()

    report = {
        "schema_id": "AEM_EVOLVE_MECH_REASON_REPORT_V1_2",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "policy_version": policy.get("version", "unknown"),
        "recommended_outcome": recommended_outcome,
        "hitl_required": hitl_required,
        "triggered_rules": triggered_rules,
        "scores": scores,
        "state_machine_validation": state_validation,
        "mechanical_explanation": explanation,
        "input_hashes": input_hashes,
        "report_hash": report_hash,
        "llm_involved": False,
        "non_claims_preserved": [
            "LLM output is not final governance.",
            "LLM output is not official status.",
            "LLM output is not regulatory approval.",
            "LLM output is not legal compliance.",
            "LLM output is not certification.",
            "LLM output is not receipt sealing.",
            "This recommendation is not regulatory approval.",
            "This recommendation is not legal compliance.",
            "This recommendation is not external certification."
        ]
    }

    V1_2.mkdir(parents=True, exist_ok=True)
    with open(REPORT_OUT, "w") as f:
        json.dump(report, f, indent=2)

    status = "PASS" if state_validation["state_transition_valid"] else "FAIL"
    print(f"MECH_REASON_STATUS={status}")
    print(f"  recommended_outcome: {recommended_outcome}")
    print(f"  hitl_required:       {hitl_required}")
    print(f"  triggered_rules:     {triggered_rules}")
