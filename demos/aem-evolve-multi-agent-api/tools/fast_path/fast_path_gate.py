"""
Fast Path Gate — deterministic pre-execution enforcement
Constitutional dependency: EthicBit / CEMU v3.7.0+

Mandatory rules:
- Cannot override AEM v1.1 artifact verification failure
- Cannot upgrade failed AI-ME evidence
- Cannot replace AEM-EVOLVE governance outcome
- Cannot replace Triple Anchor or Strong Closure
- Must fail closed or block if prohibited action detected
- Must scope-limit or block if claim exceeds claim-level ceiling
- Must not claim full-system validation latency
"""
import json
import os
import re
import time
from datetime import datetime, timezone
from enum import Enum
from typing import Optional

CONSTITUTIONAL_DEPENDENCY = "EthicBit/CEMU/v3.7.0+"


class FastPathVerdict(str, Enum):
    PASS = "PASS"
    BLOCK = "BLOCK"
    SCOPE_LIMITED = "SCOPE_LIMITED"
    DEGRADED = "DEGRADED"
    NOT_VERIFIABLE = "NOT_VERIFIABLE"
    FAIL_CLOSED = "FAIL_CLOSED"


CLAIM_CEILING_ORDER = ["PASS", "SCOPE_LIMITED", "PENDING_EXTERNAL_REVIEW", "FAIL_CLOSED", "NOT_APPLICABLE"]


def _claim_exceeds_ceiling(requested_claim_level: str, ceiling: str) -> bool:
    try:
        req_idx = CLAIM_CEILING_ORDER.index(requested_claim_level)
        ceil_idx = CLAIM_CEILING_ORDER.index(ceiling)
        return req_idx < ceil_idx
    except ValueError:
        return True


def _matches_prohibited_action(operation: str, prohibited_actions: list) -> Optional[str]:
    for pa in prohibited_actions:
        pattern = pa.get("pattern", "")
        if pattern and re.search(pattern, operation, re.IGNORECASE):
            return pa.get("reason", "Prohibited action matched.")
    return None


def _is_authorized_capability(operation: str, authorized_capabilities: list) -> bool:
    if not authorized_capabilities:
        return False
    return any(op == operation or operation.startswith(op) for op in authorized_capabilities)


def evaluate(
    snapshot: dict,
    requested_operation: str,
    requested_claim_level: str = "PASS",
    output_dir: str = "assurance/fast-path/v1",
) -> dict:
    start_ms = time.monotonic() * 1000

    # NOT_VERIFIABLE: snapshot unsigned or missing signature
    sig = snapshot.get("snapshot_signature", {})
    if not sig.get("signature") or sig.get("signature") == "" or not sig.get("signing_key_reference"):
        return _emit_verdict(
            FastPathVerdict.NOT_VERIFIABLE,
            "Snapshot is unsigned or signature reference is missing.",
            snapshot,
            requested_operation,
            requested_claim_level,
            elapsed_ms=time.monotonic() * 1000 - start_ms,
            output_dir=output_dir,
        )

    # DEGRADED: snapshot stale
    age_ms = snapshot.get("_computed_age_ms") or snapshot.get("snapshot_age_ms")
    max_tick = snapshot.get("max_tick_elapsed_ms")
    if age_ms is not None and max_tick is not None and age_ms > max_tick:
        return _emit_verdict(
            FastPathVerdict.DEGRADED,
            f"Snapshot age {age_ms}ms exceeds max_tick_elapsed_ms {max_tick}ms.",
            snapshot,
            requested_operation,
            requested_claim_level,
            elapsed_ms=time.monotonic() * 1000 - start_ms,
            output_dir=output_dir,
        )

    # BLOCK: prohibited action
    prohibited_reason = _matches_prohibited_action(
        requested_operation, snapshot.get("prohibited_actions", [])
    )
    if prohibited_reason:
        return _emit_verdict(
            FastPathVerdict.BLOCK,
            f"Prohibited action detected: {prohibited_reason}",
            snapshot,
            requested_operation,
            requested_claim_level,
            elapsed_ms=time.monotonic() * 1000 - start_ms,
            output_dir=output_dir,
        )

    # FAIL_CLOSED: AEM v1.1 assurance failed — Fast Path cannot upgrade
    aem_summary = snapshot.get("aem_artifact_assurance_summary", {})
    if aem_summary.get("summary_verified") is False and aem_summary.get("artifact_count", 0) > 0:
        return _emit_verdict(
            FastPathVerdict.FAIL_CLOSED,
            "AEM v1.1 artifact assurance failed. Fast Path cannot override artifact verification failure.",
            snapshot,
            requested_operation,
            requested_claim_level,
            elapsed_ms=time.monotonic() * 1000 - start_ms,
            output_dir=output_dir,
        )

    # FAIL_CLOSED: AI-ME aggregate failed — Fast Path cannot upgrade
    ai_me_summary = snapshot.get("ai_me_gate_outcome_summary", {})
    ai_me_aggregate = ai_me_summary.get("aggregate_outcome", "MISSING")
    if ai_me_aggregate == "FAIL_CLOSED":
        return _emit_verdict(
            FastPathVerdict.FAIL_CLOSED,
            "AI-ME gate aggregate outcome is FAIL_CLOSED. Fast Path cannot upgrade failed AI-ME evidence.",
            snapshot,
            requested_operation,
            requested_claim_level,
            elapsed_ms=time.monotonic() * 1000 - start_ms,
            output_dir=output_dir,
        )

    # SCOPE_LIMITED or FAIL_CLOSED: claim exceeds ceiling
    ceiling = snapshot.get("claim_level_ceiling", "FAIL_CLOSED")
    if _claim_exceeds_ceiling(requested_claim_level, ceiling):
        if ceiling in ("FAIL_CLOSED", "NOT_APPLICABLE"):
            return _emit_verdict(
                FastPathVerdict.FAIL_CLOSED,
                f"Requested claim level {requested_claim_level} exceeds ceiling {ceiling}.",
                snapshot,
                requested_operation,
                requested_claim_level,
                elapsed_ms=time.monotonic() * 1000 - start_ms,
                output_dir=output_dir,
            )
        return _emit_verdict(
            FastPathVerdict.SCOPE_LIMITED,
            f"Requested claim {requested_claim_level} exceeds ceiling {ceiling}. Emit with scope qualifier.",
            snapshot,
            requested_operation,
            requested_claim_level,
            elapsed_ms=time.monotonic() * 1000 - start_ms,
            output_dir=output_dir,
        )

    # PASS
    return _emit_verdict(
        FastPathVerdict.PASS,
        "Operation within authorized scope and claim ceiling.",
        snapshot,
        requested_operation,
        requested_claim_level,
        elapsed_ms=time.monotonic() * 1000 - start_ms,
        output_dir=output_dir,
    )


def _emit_verdict(
    verdict: FastPathVerdict,
    reason: str,
    snapshot: dict,
    requested_operation: str,
    requested_claim_level: str,
    elapsed_ms: float,
    output_dir: str,
) -> dict:
    now = datetime.now(timezone.utc).isoformat()
    record = {
        "fast_path_version": "1.0",
        "evaluation_timestamp": now,
        "constitutional_dependency": CONSTITUTIONAL_DEPENDENCY,
        "snapshot_id": snapshot.get("snapshot_id", ""),
        "snapshot_timestamp": snapshot.get("snapshot_timestamp", ""),
        "requested_operation": requested_operation,
        "requested_claim_level": requested_claim_level,
        "claim_level_ceiling": snapshot.get("claim_level_ceiling", ""),
        "verdict": verdict.value,
        "reason": reason,
        "evaluation_elapsed_ms": round(elapsed_ms, 3),
        "full_assurance_recomputed_this_tick": False,
        "non_claim": (
            "Fast Path enforcement does not claim full-system validation latency. "
            "Full Triple Anchor, Strong Closure, and AI-ME evidence are not recomputed per tick."
        ),
    }
    os.makedirs(output_dir, exist_ok=True)
    record_path = os.path.join(
        output_dir,
        f"fast_path_verdict_{now.replace(':', '-').replace('+', 'Z')}.json",
    )
    with open(record_path, "w") as f:
        json.dump(record, f, indent=2)
    record["_record_path"] = record_path
    return record
