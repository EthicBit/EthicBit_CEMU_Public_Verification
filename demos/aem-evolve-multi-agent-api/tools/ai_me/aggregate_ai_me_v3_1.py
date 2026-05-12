"""
AI-ME v3.1 Aggregator — AEM-EVOLVE Mechanical Ethics Assurance
Constitutional dependency: EthicBit / CEMU v3.7.0+

Aggregation rules:
- If artifact_assurance_required=true and artifact_assurance.artifact_verified=false,
  gate_outcome cannot be PASS.
- Fast Path PASS cannot upgrade a failed artifact assurance, failed AI-ME gate,
  failed Triple Anchor or failed Strong Closure.
"""
import json
import os
from typing import Optional
from .common import (
    CONSTITUTIONAL_DEPENDENCY,
    SCHEMA_VERSION,
    GateOutcome,
    timestamp_utc,
    write_gate_report,
)

AGGREGATE_NON_CLAIM = (
    "This aggregator does not claim AI-ME evidence completion, AI-ME PASS status, "
    "external validation, certification or production readiness."
)


def _load_report(path: str) -> Optional[dict]:
    if not os.path.isfile(path):
        return None
    with open(path, "r") as f:
        return json.load(f)


def _validate_gate_outcome(report: dict) -> GateOutcome:
    """Enforce: artifact_assurance_required=true + artifact_verified=false => not PASS."""
    outcome_str = report.get("gate_outcome", GateOutcome.MISSING.value)
    artifact_required = report.get("artifact_assurance_required", False)
    artifact_status = report.get("artifact_assurance_status", "FAIL")
    artifact_verified = report.get("artifact_assurance", {}).get("artifact_verified", False)

    if artifact_required and not artifact_verified:
        if outcome_str == GateOutcome.PASS.value:
            return GateOutcome.FAIL_CLOSED
    try:
        return GateOutcome(outcome_str)
    except ValueError:
        return GateOutcome.MISSING


def _fast_path_cannot_upgrade(
    fast_path_verdict: str, gate_outcome: GateOutcome
) -> bool:
    """
    Fast Path PASS cannot upgrade a failed artifact assurance or failed AI-ME gate.
    Returns True if Fast Path verdict is being used to attempt an illegal upgrade.
    """
    if fast_path_verdict == "PASS" and gate_outcome in (
        GateOutcome.FAIL_CLOSED,
        GateOutcome.MISSING,
    ):
        return True
    return False


def _determine_aggregate_outcome(gate_outcomes: list) -> GateOutcome:
    outcomes = [GateOutcome(o) for o in gate_outcomes]
    if any(o == GateOutcome.FAIL_CLOSED for o in outcomes):
        return GateOutcome.FAIL_CLOSED
    if any(o == GateOutcome.MISSING for o in outcomes):
        return GateOutcome.SCOPE_LIMITED
    if any(o == GateOutcome.SCOPE_LIMITED for o in outcomes):
        return GateOutcome.SCOPE_LIMITED
    if any(o == GateOutcome.PENDING_EXTERNAL_REVIEW for o in outcomes):
        return GateOutcome.PENDING_EXTERNAL_REVIEW
    if all(o in (GateOutcome.PASS, GateOutcome.NOT_APPLICABLE_WITH_JUSTIFICATION) for o in outcomes):
        return GateOutcome.PASS
    return GateOutcome.SCOPE_LIMITED


def aggregate(
    report_dir: str = "assurance/ai-me/v3_1",
    output_path: Optional[str] = None,
) -> dict:
    gate_ids = [f"AI-ME-{str(i).zfill(2)}" for i in range(1, 13)]
    gate_summaries = []
    fast_path_illegal_upgrades = []

    for gate_id in gate_ids:
        report_path = os.path.join(report_dir, f"{gate_id}_report.json")
        report = _load_report(report_path)

        if report is None:
            gate_summaries.append({
                "gate_id": gate_id,
                "gate_outcome": GateOutcome.MISSING.value,
                "artifact_assurance_required": True,
                "artifact_assurance_status": "MISSING",
                "artifact_verified": False,
                "verification_receipts": [],
                "public_anchor_references": [],
                "claim_boundary_result": None,
                "fast_path_enabled": False,
                "fast_path_pre_execution_verdict": "NOT_APPLICABLE",
                "fast_path_full_assurance_recalculated_per_tick": False,
                "constitutional_dependency": CONSTITUTIONAL_DEPENDENCY,
                "report_found": False,
            })
            continue

        validated_outcome = _validate_gate_outcome(report)
        art_assurance = report.get("artifact_assurance", {})
        fp = report.get("fast_path", {})
        fp_verdict = fp.get("pre_execution_verdict", "NOT_APPLICABLE")
        fp_full_recalc = fp.get("full_assurance_recalculated_per_tick", False)

        if _fast_path_cannot_upgrade(fp_verdict, validated_outcome):
            fast_path_illegal_upgrades.append({
                "gate_id": gate_id,
                "fast_path_verdict": fp_verdict,
                "validated_gate_outcome": validated_outcome.value,
                "violation": "Fast Path PASS cannot upgrade failed gate outcome",
            })
            validated_outcome = GateOutcome.FAIL_CLOSED

        gate_summaries.append({
            "gate_id": gate_id,
            "gate_name": report.get("gate_name", ""),
            "gate_outcome": validated_outcome.value,
            "artifact_assurance_required": report.get("artifact_assurance_required", False),
            "artifact_assurance_status": report.get("artifact_assurance_status", "UNKNOWN"),
            "artifact_verified": art_assurance.get("artifact_verified", False),
            "verification_receipts": art_assurance.get("verification_receipts", []),
            "public_anchor_references": art_assurance.get("public_anchor_references", []),
            "claim_boundary_result": report.get("claim_boundary_result"),
            "fast_path_enabled": fp.get("enabled", False),
            "fast_path_pre_execution_verdict": fp_verdict,
            "fast_path_full_assurance_recalculated_per_tick": fp_full_recalc,
            "constitutional_dependency": CONSTITUTIONAL_DEPENDENCY,
            "report_found": True,
        })

    aggregate_outcome = _determine_aggregate_outcome(
        [g["gate_outcome"] for g in gate_summaries]
    )

    aggregate_report = {
        "schema_version": SCHEMA_VERSION,
        "report_type": "AI_ME_V3_1_AGGREGATE",
        "aggregation_timestamp": timestamp_utc(),
        "constitutional_dependency": CONSTITUTIONAL_DEPENDENCY,
        "aggregate_outcome": aggregate_outcome.value,
        "gates_evaluated": len(gate_summaries),
        "gates_pass": sum(1 for g in gate_summaries if g["gate_outcome"] == GateOutcome.PASS.value),
        "gates_scope_limited": sum(1 for g in gate_summaries if g["gate_outcome"] == GateOutcome.SCOPE_LIMITED.value),
        "gates_fail_closed": sum(1 for g in gate_summaries if g["gate_outcome"] == GateOutcome.FAIL_CLOSED.value),
        "gates_missing": sum(1 for g in gate_summaries if g["gate_outcome"] == GateOutcome.MISSING.value),
        "gates_pending": sum(1 for g in gate_summaries if g["gate_outcome"] == GateOutcome.PENDING_EXTERNAL_REVIEW.value),
        "fast_path_illegal_upgrade_violations": fast_path_illegal_upgrades,
        "aggregation_rules_applied": [
            "artifact_assurance_required=true AND artifact_verified=false => outcome cannot be PASS",
            "Fast Path PASS cannot upgrade failed artifact assurance or failed gate outcome",
        ],
        "gate_summaries": gate_summaries,
        "non_claim": AGGREGATE_NON_CLAIM,
    }

    out_path = output_path or os.path.join(report_dir, "AI_ME_V3_1_AGGREGATE_REPORT.json")
    write_gate_report(aggregate_report, out_path)
    return aggregate_report
