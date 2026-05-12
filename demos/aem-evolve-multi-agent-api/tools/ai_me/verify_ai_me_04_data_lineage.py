"""
AI-ME-04 — Data Provenance & Lineage Evidence
AEM-EVOLVE v3.1 — Specification Release scaffold
Constitutional dependency: EthicBit / CEMU v3.7.0+
"""
import os
from typing import List
from .common import (
    CONSTITUTIONAL_DEPENDENCY,
    SCHEMA_VERSION,
    GateOutcome,
    artifact_assurance_block,
    constitutional_dependency_block,
    fail_closed_if_required_artifact_missing,
    fast_path_metadata,
    FastPathVerdict,
    timestamp_utc,
    verify_artifact_hash,
    write_gate_report,
    write_verification_receipt,
)

GATE_ID = "AI-ME-04"
GATE_NAME = "Data Provenance & Lineage Evidence"
ALLOWED_CLAIM = (
    "Data provenance evidence exists for [dataset] within [scope] as of [date]."
)
NON_CLAIM = (
    "This gate does not claim legal data compliance, complete lineage coverage, "
    "or data quality certification."
)


def verify(
    lineage_artifact_path: str,
    declared_hash: str,
    data_sources: List[str],
    lineage_scope: str,
    fast_path_enabled: bool = False,
    snapshot_reference: str = "",
    manifest_path: str = "",
    output_dir: str = "assurance/ai-me/v3_1",
) -> dict:
    artifact_verified = False
    verification_receipts = []
    artifact_hashes = []

    if os.path.isfile(lineage_artifact_path):
        artifact_verified = verify_artifact_hash(lineage_artifact_path, declared_hash)
        artifact_hashes = [
            {
                "artifact_id": "data_lineage_graph",
                "algorithm": "sha256",
                "hash": declared_hash,
            }
        ]
        receipt_path = write_verification_receipt(
            gate_id=GATE_ID,
            artifact_id="data_lineage_graph",
            artifact_path=lineage_artifact_path,
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
        outcome_reason = "Required data lineage artifact is missing or unverified by AEM v1.1."
        claim_ceiling = "FAIL_CLOSED"
        fp_verdict = FastPathVerdict.FAIL_CLOSED
    elif not data_sources:
        outcome = GateOutcome.SCOPE_LIMITED
        outcome_reason = "Data sources not declared."
        claim_ceiling = "SCOPE_LIMITED"
        fp_verdict = FastPathVerdict.SCOPE_LIMITED
    else:
        outcome = GateOutcome.PASS
        outcome_reason = "Data lineage artifact verified. Sources declared."
        claim_ceiling = "PASS"
        fp_verdict = FastPathVerdict.PASS

    fp = fast_path_metadata(
        enabled=fast_path_enabled,
        snapshot_reference=snapshot_reference,
        pre_execution_verdict=fp_verdict if fast_path_enabled else FastPathVerdict.NOT_APPLICABLE,
        fast_path_scope="data_provenance_snapshot_inheritance" if fast_path_enabled else "",
    )

    report = {
        "schema_version": SCHEMA_VERSION,
        "gate_id": GATE_ID,
        "gate_name": GATE_NAME,
        "evaluation_timestamp": timestamp_utc(),
        "data_sources": data_sources,
        "lineage_scope": lineage_scope,
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
            "scope_qualifier": lineage_scope,
        },
        "fast_path": fp,
        "allowed_claim": ALLOWED_CLAIM,
        "non_claim": NON_CLAIM,
        **constitutional_dependency_block(),
    }

    report_path = os.path.join(output_dir, f"{GATE_ID}_report.json")
    write_gate_report(report, report_path)
    return report
