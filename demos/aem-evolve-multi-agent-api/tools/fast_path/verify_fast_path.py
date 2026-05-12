"""
Fast Path verification — scaffold verification runner
Constitutional dependency: EthicBit / CEMU v3.7.0+
"""
import json
import os
from .fast_path_snapshot import load_and_validate, SnapshotValidationError, create_scaffold_snapshot
from .fast_path_gate import evaluate, FastPathVerdict

CONSTITUTIONAL_DEPENDENCY = "EthicBit/CEMU/v3.7.0+"
NON_CLAIM = (
    "This verification does not claim production readiness, full-system validation, "
    "external certification, or that Fast Path subsumes the complete governance stack."
)


def verify_from_snapshot_file(
    snapshot_path: str,
    requested_operation: str = "emit_output",
    requested_claim_level: str = "PASS",
    output_dir: str = "assurance/fast-path/v1",
) -> dict:
    try:
        snapshot = load_and_validate(snapshot_path)
    except SnapshotValidationError as e:
        return {
            "verdict": FastPathVerdict.NOT_VERIFIABLE.value,
            "reason": str(e),
            "constitutional_dependency": CONSTITUTIONAL_DEPENDENCY,
            "non_claim": NON_CLAIM,
        }
    return evaluate(
        snapshot=snapshot,
        requested_operation=requested_operation,
        requested_claim_level=requested_claim_level,
        output_dir=output_dir,
    )


def verify_scaffold(
    output_dir: str = "assurance/fast-path/v1",
) -> dict:
    """Run scaffold verification with a test snapshot. For CI / spec validation only."""
    snapshot = create_scaffold_snapshot(
        claim_level_ceiling="SCOPE_LIMITED",
        authorized_capabilities=["emit_output", "read_memory"],
        prohibited_actions=[
            {"pattern": "delete_all", "reason": "Bulk delete is prohibited"},
            {"pattern": "bypass_hitl", "reason": "HITL bypass is constitutionally prohibited"},
        ],
        max_tick_elapsed_ms=10000,
    )
    snapshot["_computed_age_ms"] = 0

    result = evaluate(
        snapshot=snapshot,
        requested_operation="emit_output",
        requested_claim_level="SCOPE_LIMITED",
        output_dir=output_dir,
    )
    result["scaffold_mode"] = True
    result["non_claim"] = NON_CLAIM
    return result


if __name__ == "__main__":
    import sys
    output_dir = "assurance/fast-path/v1"
    if len(sys.argv) > 1 and os.path.isfile(sys.argv[1]):
        result = verify_from_snapshot_file(sys.argv[1], output_dir=output_dir)
    else:
        result = verify_scaffold(output_dir=output_dir)
    print(json.dumps(result, indent=2))
