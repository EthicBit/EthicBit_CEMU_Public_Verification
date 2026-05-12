"""
AI-ME common utilities — AEM-EVOLVE v3.1
Constitutional dependency: EthicBit / CEMU v3.7.0+
"""
import hashlib
import json
import os
from datetime import datetime, timezone
from enum import Enum
from typing import Optional


class GateOutcome(str, Enum):
    PASS = "PASS"
    SCOPE_LIMITED = "SCOPE_LIMITED"
    FAIL_CLOSED = "FAIL_CLOSED"
    NOT_APPLICABLE_WITH_JUSTIFICATION = "NOT_APPLICABLE_WITH_JUSTIFICATION"
    MISSING = "MISSING"
    PENDING_EXTERNAL_REVIEW = "PENDING_EXTERNAL_REVIEW"


class FastPathVerdict(str, Enum):
    PASS = "PASS"
    BLOCK = "BLOCK"
    SCOPE_LIMITED = "SCOPE_LIMITED"
    DEGRADED = "DEGRADED"
    NOT_VERIFIABLE = "NOT_VERIFIABLE"
    FAIL_CLOSED = "FAIL_CLOSED"
    NOT_APPLICABLE = "NOT_APPLICABLE"


CONSTITUTIONAL_DEPENDENCY = "EthicBit/CEMU/v3.7.0+"
AEM_VERSION = "v1.1"
SCHEMA_VERSION = "3.1"


def timestamp_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_file(path: str) -> Optional[str]:
    if not os.path.isfile(path):
        return None
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def verify_artifact_hash(artifact_path: str, declared_hash: str) -> bool:
    computed = sha256_file(artifact_path)
    if computed is None:
        return False
    return computed == declared_hash


def load_artifact_manifest(manifest_path: str) -> dict:
    if not os.path.isfile(manifest_path):
        return {}
    with open(manifest_path, "r") as f:
        return json.load(f)


def write_verification_receipt(
    gate_id: str,
    artifact_id: str,
    artifact_path: str,
    artifact_hash: str,
    verified: bool,
    output_dir: str,
) -> str:
    receipt = {
        "receipt_type": "aem_v1_1_verification_receipt",
        "aem_version": AEM_VERSION,
        "gate_id": gate_id,
        "artifact_id": artifact_id,
        "artifact_path": artifact_path,
        "artifact_hash": artifact_hash,
        "artifact_verified": verified,
        "constitutional_dependency": CONSTITUTIONAL_DEPENDENCY,
        "timestamp": timestamp_utc(),
    }
    os.makedirs(output_dir, exist_ok=True)
    receipt_path = os.path.join(output_dir, f"receipt_{gate_id}_{artifact_id}.json")
    with open(receipt_path, "w") as f:
        json.dump(receipt, f, indent=2)
    return receipt_path


def fail_closed_if_required_artifact_missing(
    gate_id: str,
    artifact_required: bool,
    artifact_verified: bool,
    reason: str = "",
) -> Optional[GateOutcome]:
    if artifact_required and not artifact_verified:
        return GateOutcome.FAIL_CLOSED
    return None


def constitutional_dependency_block() -> dict:
    return {
        "constitutional_dependency": CONSTITUTIONAL_DEPENDENCY,
        "technology_subordination_rule": (
            "The technology stack does not replace the EthicBit / CEMU "
            "constitutional-operational regime. It operationalizes it."
        ),
    }


def fast_path_metadata(
    enabled: bool = False,
    snapshot_reference: str = "",
    snapshot_freshness_ms: Optional[int] = None,
    pre_execution_verdict: FastPathVerdict = FastPathVerdict.NOT_APPLICABLE,
    max_tick_elapsed_ms: Optional[int] = None,
    fast_path_scope: str = "",
) -> dict:
    return {
        "enabled": enabled,
        "snapshot_reference": snapshot_reference,
        "snapshot_freshness_ms": snapshot_freshness_ms,
        "pre_execution_verdict": pre_execution_verdict.value,
        "max_tick_elapsed_ms": max_tick_elapsed_ms,
        "full_assurance_recalculated_per_tick": False,
        "fast_path_scope": fast_path_scope,
    }


def artifact_assurance_block(
    artifact_verified: bool = False,
    artifact_manifest: str = "",
    artifact_hashes: Optional[list] = None,
    verification_receipts: Optional[list] = None,
    public_anchor_references: Optional[list] = None,
) -> dict:
    return {
        "aem_version": AEM_VERSION,
        "artifact_verified": artifact_verified,
        "artifact_manifest": artifact_manifest,
        "artifact_hashes": artifact_hashes or [],
        "verification_receipts": verification_receipts or [],
        "public_anchor_references": public_anchor_references or [],
    }


def write_gate_report(report: dict, output_path: str) -> None:
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(report, f, indent=2)
