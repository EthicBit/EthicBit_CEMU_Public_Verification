"""
AI-ME-05 — Agent Trace Capture Evidence
AEM-EVOLVE v3.1 — Evidence Execution
Constitutional dependency: EthicBit / CEMU v3.7.0+
Note: Raw chain-of-thought capture is prohibited. Rationale summary and planning metadata only.
"""
import os
from .common import (
    CONSTITUTIONAL_DEPENDENCY, SCHEMA_VERSION, GateOutcome,
    artifact_assurance_block, constitutional_dependency_block,
    fail_closed_if_required_artifact_missing, fast_path_metadata,
    timestamp_utc, verify_artifact_hash, write_gate_report, write_verification_receipt,
)

GATE_ID = "AI-ME-05"
GATE_NAME = "Agent Trace Capture Evidence"
ALLOWED_CLAIM = "Agent trace evidence exists for [operation] within [scope] as of [date]."
NON_CLAIM = (
    "This gate does not claim complete agent interpretability, full chain-of-thought capture, "
    "or real-time tracing. Raw chain-of-thought is prohibited evidence."
)


def verify(
    trace_artifact_path: str,
    declared_hash: str,
    operation_scope: str,
    raw_cot_captured: bool = False,
    manifest_path: str = "",
    output_dir: str = "assurance/ai-me/v3_1",
) -> dict:
    artifact_verified = False
    verification_receipts = []
    artifact_hashes = []

    if raw_cot_captured:
        report = {
            "schema_version": SCHEMA_VERSION,
            "gate_id": GATE_ID,
            "gate_name": GATE_NAME,
            "evaluation_timestamp": timestamp_utc(),
            "operation_scope": operation_scope,
            "constitutional_dependency": CONSTITUTIONAL_DEPENDENCY,
            "artifact_assurance_required": True,
            "artifact_assurance_status": "FAIL",
            "artifact_assurance": artifact_assurance_block(),
            "gate_outcome": GateOutcome.FAIL_CLOSED.value,
            "gate_outcome_reason": "Raw chain-of-thought capture is prohibited per AI-ME-05.",
            "claim_boundary_result": {
                "claim_class": "PROHIBITED_CLAIM",
                "claim_level_ceiling": "FAIL_CLOSED",
                "allowed_emission": False,
                "scope_qualifier": operation_scope,
            },
            "fast_path": fast_path_metadata(),
            "allowed_claim": ALLOWED_CLAIM,
            "non_claim": NON_CLAIM,
            **constitutional_dependency_block(),
        }
        report_path = os.path.join(output_dir, f"{GATE_ID}_report.json")
        write_gate_report(report, report_path)
        return report

    if os.path.isfile(trace_artifact_path):
        artifact_verified = verify_artifact_hash(trace_artifact_path, declared_hash)
        artifact_hashes = [{"artifact_id": "agent_trace_artifact", "algorithm": "sha256", "hash": declared_hash}]
        receipt_path = write_verification_receipt(
            gate_id=GATE_ID, artifact_id="agent_trace_artifact",
            artifact_path=trace_artifact_path, artifact_hash=declared_hash,
            verified=artifact_verified, output_dir=output_dir,
        )
        verification_receipts = [receipt_path]

    forced_fail = fail_closed_if_required_artifact_missing(
        gate_id=GATE_ID, artifact_required=True, artifact_verified=artifact_verified,
    )

    if forced_fail:
        outcome = GateOutcome.FAIL_CLOSED
        outcome_reason = "Required agent trace artifact is missing or unverified by AEM v1.1."
        claim_ceiling = "FAIL_CLOSED"
    elif not operation_scope:
        outcome = GateOutcome.SCOPE_LIMITED
        outcome_reason = "Operation scope not declared."
        claim_ceiling = "SCOPE_LIMITED"
    else:
        outcome = GateOutcome.PASS
        outcome_reason = "Agent trace artifact verified. Rationale summary and planning metadata present. Scope declared."
        claim_ceiling = "PASS"

    report = {
        "schema_version": SCHEMA_VERSION,
        "gate_id": GATE_ID,
        "gate_name": GATE_NAME,
        "evaluation_timestamp": timestamp_utc(),
        "operation_scope": operation_scope,
        "raw_cot_captured": False,
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
            "scope_qualifier": operation_scope,
        },
        "fast_path": fast_path_metadata(fast_path_scope="trace_metadata_snapshot"),
        "allowed_claim": ALLOWED_CLAIM,
        "non_claim": NON_CLAIM,
        **constitutional_dependency_block(),
    }

    report_path = os.path.join(output_dir, f"{GATE_ID}_report.json")
    write_gate_report(report, report_path)
    return report
