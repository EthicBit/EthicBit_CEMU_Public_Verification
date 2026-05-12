"""
AI-ME-03 — Explainability Artifact Evidence
AEM-EVOLVE v3.1 — Specification Release scaffold
Constitutional dependency: EthicBit / CEMU v3.7.0+
"""
import os
from .common import (
    CONSTITUTIONAL_DEPENDENCY,
    SCHEMA_VERSION,
    GateOutcome,
    artifact_assurance_block,
    constitutional_dependency_block,
    fail_closed_if_required_artifact_missing,
    fast_path_metadata,
    timestamp_utc,
    verify_artifact_hash,
    write_gate_report,
    write_verification_receipt,
)

GATE_ID = "AI-ME-03"
GATE_NAME = "Explainability Artifact Evidence"
ALLOWED_CLAIM = (
    "Explainability artifacts exist for [model] using [methodology] within [scope]."
)
NON_CLAIM = (
    "This gate does not claim full model interpretability, regulatory explainability "
    "compliance, or universal applicability."
)


def verify(
    explainability_artifact_path: str,
    declared_hash: str,
    methodology: str,
    application_scope: str,
    manifest_path: str = "",
    output_dir: str = "assurance/ai-me/v3_1",
) -> dict:
    artifact_verified = False
    verification_receipts = []
    artifact_hashes = []

    if os.path.isfile(explainability_artifact_path):
        artifact_verified = verify_artifact_hash(
            explainability_artifact_path, declared_hash
        )
        artifact_hashes = [
            {
                "artifact_id": "explainability_artifact",
                "algorithm": "sha256",
                "hash": declared_hash,
            }
        ]
        receipt_path = write_verification_receipt(
            gate_id=GATE_ID,
            artifact_id="explainability_artifact",
            artifact_path=explainability_artifact_path,
            artifact_hash=declared_hash,
            verified=artifact_verified,
            output_dir=output_dir,
        )
        verification_receipts = [receipt_path]

    forced_fail = fail_closed_if_required_artifact_missing(
        gate_id=GATE_ID,
        artifact_required=True,
        artifact_verified=artifact_verified,
    )

    if forced_fail:
        outcome = GateOutcome.FAIL_CLOSED
        outcome_reason = "Required explainability artifact is missing or unverified by AEM v1.1."
        claim_ceiling = "FAIL_CLOSED"
    elif not methodology:
        outcome = GateOutcome.SCOPE_LIMITED
        outcome_reason = "Explainability methodology not declared."
        claim_ceiling = "SCOPE_LIMITED"
    else:
        outcome = GateOutcome.PASS
        outcome_reason = "Explainability artifact verified. Methodology declared."
        claim_ceiling = "PASS"

    report = {
        "schema_version": SCHEMA_VERSION,
        "gate_id": GATE_ID,
        "gate_name": GATE_NAME,
        "evaluation_timestamp": timestamp_utc(),
        "methodology": methodology,
        "application_scope": application_scope,
        "constitutional_dependency": CONSTITUTIONAL_DEPENDENCY,
        "artifact_assurance_required": True,
        "artifact_assurance_status": "PASS" if artifact_verified else "FAIL",
        "artifact_assurance": artifact_assurance_block(
            artifact_verified=artifact_verified,
            artifact_manifest=manifest_path,
            artifact_hashes=artifact_hashes,
            verification_receipts=verification_receipts,
        ),
        "gate_outcome": outcome.value,
        "gate_outcome_reason": outcome_reason,
        "claim_boundary_result": {
            "claim_class": "FULL_CLAIM" if outcome == GateOutcome.PASS else "SCOPED_CLAIM",
            "claim_level_ceiling": claim_ceiling,
            "allowed_emission": outcome != GateOutcome.FAIL_CLOSED,
            "scope_qualifier": application_scope,
        },
        "fast_path": fast_path_metadata(),
        "allowed_claim": ALLOWED_CLAIM,
        "non_claim": NON_CLAIM,
        **constitutional_dependency_block(),
    }

    report_path = os.path.join(output_dir, f"{GATE_ID}_report.json")
    write_gate_report(report, report_path)
    return report
