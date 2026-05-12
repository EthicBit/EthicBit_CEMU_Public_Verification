"""
Fast Path Snapshot — canonical snapshot loader and validator
Constitutional dependency: EthicBit / CEMU v3.7.0+
"""
import hashlib
import json
import os
import time
from datetime import datetime, timezone
from typing import Optional

CONSTITUTIONAL_DEPENDENCY = "EthicBit/CEMU/v3.7.0+"
AEM_VERSION = "v1.1"
SCHEMA_VERSION = "1.0"


class SnapshotValidationError(Exception):
    pass


def _load_snapshot(snapshot_path: str) -> dict:
    if not os.path.isfile(snapshot_path):
        raise SnapshotValidationError(f"Snapshot not found: {snapshot_path}")
    with open(snapshot_path, "r") as f:
        return json.load(f)


def _validate_constitutional_dependency(snapshot: dict) -> None:
    dep = snapshot.get("constitutional_dependency")
    if dep != CONSTITUTIONAL_DEPENDENCY:
        raise SnapshotValidationError(
            f"Constitutional dependency mismatch: expected {CONSTITUTIONAL_DEPENDENCY}, got {dep}"
        )


def _validate_signature_present(snapshot: dict) -> bool:
    sig = snapshot.get("snapshot_signature", {})
    return bool(sig.get("signature") and sig.get("signing_key_reference"))


def _compute_snapshot_age_ms(snapshot: dict) -> Optional[int]:
    ts_str = snapshot.get("snapshot_timestamp")
    if not ts_str:
        return None
    try:
        ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
        now = datetime.now(timezone.utc)
        return int((now - ts).total_seconds() * 1000)
    except Exception:
        return None


def _validate_full_assurance_flag(snapshot: dict) -> None:
    """Enforce: full_assurance_recomputed_per_tick must be False."""
    if snapshot.get("full_assurance_recomputed_per_tick", True) is not False:
        raise SnapshotValidationError(
            "Invalid snapshot: full_assurance_recomputed_per_tick must be false. "
            "Fast Path does not recompute full Triple Anchor, Strong Closure, or AI-ME evidence per tick."
        )


def load_and_validate(snapshot_path: str) -> dict:
    snapshot = _load_snapshot(snapshot_path)
    _validate_constitutional_dependency(snapshot)
    _validate_full_assurance_flag(snapshot)
    if not _validate_signature_present(snapshot):
        raise SnapshotValidationError("Snapshot is unsigned or missing signing key reference.")
    age_ms = _compute_snapshot_age_ms(snapshot)
    snapshot["_computed_age_ms"] = age_ms
    return snapshot


def create_scaffold_snapshot(
    claim_level_ceiling: str = "SCOPE_LIMITED",
    authorized_capabilities: Optional[list] = None,
    prohibited_actions: Optional[list] = None,
    max_tick_elapsed_ms: int = 5000,
) -> dict:
    now = datetime.now(timezone.utc).isoformat()
    content = {
        "schema_version": SCHEMA_VERSION,
        "snapshot_id": f"snapshot_{int(time.time())}",
        "snapshot_timestamp": now,
        "snapshot_age_ms": 0,
        "max_tick_elapsed_ms": max_tick_elapsed_ms,
        "constitutional_dependency": CONSTITUTIONAL_DEPENDENCY,
        "claim_level_ceiling": claim_level_ceiling,
        "authorized_capabilities": authorized_capabilities or [],
        "prohibited_actions": prohibited_actions or [],
        "constitutional_equivalence_hash": "",
        "aem_artifact_assurance_summary": {
            "aem_version": AEM_VERSION,
            "summary_verified": False,
            "artifact_count": 0,
            "artifacts_verified": 0,
            "summary_hash": "",
        },
        "ai_me_gate_outcome_summary": {
            "summary_timestamp": now,
            "gates_evaluated": 0,
            "aggregate_outcome": "MISSING",
            "gate_outcomes": {},
        },
        "snapshot_signature": {
            "algorithm": "scaffold",
            "signature": "SCAFFOLD_NOT_SIGNED",
            "signing_key_reference": "SCAFFOLD",
        },
        "full_assurance_recomputed_per_tick": False,
    }
    content_hash = hashlib.sha256(
        json.dumps(content, sort_keys=True).encode()
    ).hexdigest()
    content["constitutional_equivalence_hash"] = content_hash
    return content
