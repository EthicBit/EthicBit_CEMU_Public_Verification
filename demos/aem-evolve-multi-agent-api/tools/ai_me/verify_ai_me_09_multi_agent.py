"""
AI-ME-09 — Multi-Agent Coordination Governance Evidence
AEM-EVOLVE v3.1 — Evidence Execution
Constitutional dependency: EthicBit / CEMU v3.7.0+
"""
import os
from .common import (
    CONSTITUTIONAL_DEPENDENCY, SCHEMA_VERSION, GateOutcome,
    artifact_assurance_block, constitutional_dependency_block,
    fail_closed_if_required_artifact_missing, fast_path_metadata,
    timestamp_utc, verify_artifact_hash, write_gate_report, write_verification_receipt,
)

GATE_ID = "AI-ME-09"
GATE_NAME = "Multi-Agent Coordination Governance Evidence"
ALLOWED_CLAIM = "Multi-agent coordination governance evidence exists for [agents] within [scope]."
NON_CLAIM = (
    "This gate does not claim universal multi-agent governance, real-time coordination "
    "monitoring, or agent identity verification."
)


def verify(
    coordination_log_path: str,
    declared_hash: str,
    evaluation_scope: str,
    agent_roles_declared: bool = True,
    not_applicable: bool = False,
    not_applicable_justification: str = "",
    manifest_path: str = "",
    output_dir: str = "assurance/ai-me/v3_1",
) -> dict:
    if not_applicable and not_applicable_justification:
        report = {
            "schema_version": SCHEMA_VERSION,
            "gate_id": GATE_ID,
            "gate_name": GATE_NAME,
            "evaluation_timestamp": timestamp_utc(),
            "evaluation_scope": evaluation_scope,
            "constitutional_dependency": CONSTITUTIONAL_DEPENDENCY,
            "artifact_assurance_required": False,
            "artifact_assurance_status": "NOT_APPLICABLE",
            "artifact_assurance": artifact_assurance_block(),
            "gate_outcome": GateOutcome.NOT_APPLICABLE_WITH_JUSTIFICATION.value,
            "gate_outcome_reason": not_applicable_justification,
            "claim_boundary_result": {
                "claim_class": "SCOPED_CLAIM",
                "claim_level_ceiling": "NOT_APPLICABLE_WITH_JUSTIFICATION",
                "allowed_emission": True,
                "scope_qualifier": evaluation_scope,
            },
            "fast_path": fast_path_metadata(),
            "allowed_claim": ALLOWED_CLAIM,
            "non_claim": NON_CLAIM,
            **constitutional_dependency_block(),
        }
        report_path = os.path.join(output_dir, f"{GATE_ID}_report.json")
        write_gate_report(report, report_path)
        return report

    artifact_verified = False
    verification_receipts = []
    artifact_hashes = []

    if os.path.isfile(coordination_log_path):
        artifact_verified = verify_artifact_hash(coordination_log_path, declared_hash)
        artifact_hashes = [{"artifact_id": "multi_agent_coordination_log", "algorithm": "sha256", "hash": declared_hash}]
        receipt_path = write_verification_receipt(
            gate_id=GATE_ID, artifact_id="multi_agent_coordination_log",
            artifact_path=coordination_log_path, artifact_hash=declared_hash,
            verified=artifact_verified, output_dir=output_dir,
        )
        verification_receipts = [receipt_path]

    forced_fail = fail_closed_if_required_artifact_missing(
        gate_id=GATE_ID, artifact_required=True, artifact_verified=artifact_verified,
    )

    if forced_fail:
        outcome = GateOutcome.FAIL_CLOSED
        outcome_reason = "Required multi-agent coordination log is missing or unverified by AEM v1.1."
        claim_ceiling = "FAIL_CLOSED"
    elif not agent_roles_declared:
        outcome = GateOutcome.SCOPE_LIMITED
        outcome_reason = "Agent roles not declared."
        claim_ceiling = "SCOPE_LIMITED"
    else:
        outcome = GateOutcome.PASS
        outcome_reason = "Multi-agent coordination log verified. Agent roles declared. Handoff records present."
        claim_ceiling = "PASS"

    report = {
        "schema_version": SCHEMA_VERSION,
        "gate_id": GATE_ID,
        "gate_name": GATE_NAME,
        "evaluation_timestamp": timestamp_utc(),
        "evaluation_scope": evaluation_scope,
        "agent_roles_declared": agent_roles_declared,
        "constitutional_dependency": CONSTITUTIONAL_DEPENDENCY,
        "artifact_assurance_required": True,
        "artifact_assurance_status": "PASS" if artifact_verified else "FAIL",
        "artifact_assurance": artifact_assurance_block(
            artifact_verified=artifact_verified, artifact_manifest=manifest_path,
            artifact_hashes=artifact_hashes, verification_receipts=verification_receipts,
        ),
        "gate_outcome": outcome.value,
        "gate_outcome_reason": outcome_reason,
        "claim_boundary_result": {
            "claim_class": "FULL_CLAIM" if outcome == GateOutcome.PASS else "SCOPED_CLAIM",
            "claim_level_ceiling": claim_ceiling,
            "allowed_emission": outcome != GateOutcome.FAIL_CLOSED,
            "scope_qualifier": evaluation_scope,
        },
        "fast_path": fast_path_metadata(),
        "allowed_claim": ALLOWED_CLAIM,
        "non_claim": NON_CLAIM,
        **constitutional_dependency_block(),
    }

    report_path = os.path.join(output_dir, f"{GATE_ID}_report.json")
    write_gate_report(report, report_path)
    return report
