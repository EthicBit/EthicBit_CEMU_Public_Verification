"""Mechanical explanation generator for MECH-REASON™ — AEM-EVOLVE™ v1.2.

Generates deterministic, rule-based explanations for governance outcomes.
No LLM involvement. Every explanation is derived purely from triggered
rules and score values.
"""
from __future__ import annotations


def generate_explanation(
    triggered_rules: list[str],
    recommended_outcome: str,
    scores: dict,
    policy_rules: list[dict],
) -> str:
    lines: list[str] = []
    policy_index = {r["rule_id"]: r for r in policy_rules}

    # Triggered rules section
    if triggered_rules:
        for rule_id in triggered_rules:
            rule = policy_index.get(rule_id, {})
            expl = rule.get("explanation", "rule triggered")
            outcome = rule.get("outcome", rule.get("outcome_if_triggered", "unknown"))
            lines.append(f"Rule {rule_id} triggered: {expl} → {outcome}.")
    else:
        lines.append("No claim boundary rules triggered.")

    # Score context
    ev = scores.get("evidence_completeness_score", 0.0)
    gr = scores.get("governance_risk_score", 0.0)
    cb = scores.get("claim_boundary_risk_score", 0.0)
    ai = scores.get("anchor_integrity_score", 0.0)
    ri = scores.get("receipt_integrity_score", 0.0)
    rm = scores.get("regulatory_mapping_presence_score", 0.0)
    hn = scores.get("hitl_necessity_score", 0.0)

    lines.append(
        f"Evidence completeness score: {ev:.3f} "
        f"({'sufficient' if ev >= 0.80 else 'partial' if ev >= 0.50 else 'insufficient'})."
    )
    lines.append(
        f"Governance risk score: {gr:.3f} "
        f"({'low' if gr <= 0.40 else 'moderate' if gr <= 0.70 else 'high'})."
    )
    lines.append(f"Claim boundary risk score: {cb:.3f}.")
    lines.append(f"Anchor integrity score: {ai:.3f}.")
    lines.append(f"Receipt integrity score: {ri:.3f}.")
    lines.append(f"Regulatory mapping presence score: {rm:.3f}.")
    lines.append(f"HITL necessity score: {hn:.3f}.")

    # Outcome rationale
    if recommended_outcome == "FAIL_CLOSED":
        lines.append(
            "Recommended outcome: FAIL_CLOSED. "
            "One or more critical claim boundary rules were violated. "
            "The MechanicalGate must deny this execution."
        )
    elif recommended_outcome == "ESCALATE_TO_HITL":
        lines.append(
            "Recommended outcome: ESCALATE_TO_HITL. "
            "Risk scores or domain sensitivity require human review before proceeding."
        )
    elif recommended_outcome == "SCOPE_LIMITED":
        lines.append(
            "Recommended outcome: SCOPE_LIMITED. "
            "Evidence or risk scores fall within the partial acceptance band. "
            "Execution is permitted within declared scope only."
        )
    else:
        lines.append(
            "Recommended outcome: PASS. "
            "All claim boundary checks passed and scores are within acceptable thresholds."
        )

    lines.append("LLM output was not used to generate this explanation.")
    return " ".join(lines)
