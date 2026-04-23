#!/usr/bin/env python3
"""Write canonical PQ runtime secret protection artifact."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DEFAULT_REQUIRED_SECTORS = "CORE,JUSTICIA,FINANZAS,SECURITY,TECHNICAL,LEGAL,REGULATORY"
DEFAULT_STRICT_CLAIM_LEVELS = "freeze_grade,sovereign_release"


def now_utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def parse_csv(value: str) -> list[str]:
    return [part.strip() for part in value.split(",") if part.strip()]


def read_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None
    return payload if isinstance(payload, dict) else None


def stable_hash(payload: dict[str, Any]) -> str:
    blob = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()


def to_repo_relative(root: Path, candidate: Path) -> str:
    try:
        return str(candidate.resolve().relative_to(root.resolve()))
    except Exception:
        return str(candidate.resolve())


def build_status(
    gate: dict[str, Any] | None,
    *,
    claim_level: str,
    strict_claim_levels: set[str],
    required_sectors: list[str],
) -> tuple[str, str, list[str], str]:
    strict_claim = claim_level in strict_claim_levels
    if gate is None:
        if strict_claim:
            return "FAIL_CLOSED", "mechanical_ethics_gate_missing", required_sectors, "UNKNOWN"
        return "UNAVAILABLE_IN_CURRENT_RUNTIME", "mechanical_ethics_gate_missing", required_sectors, "UNKNOWN"

    gate_status = str(gate.get("status") or "UNKNOWN").upper()
    gate_mode = str(gate.get("mode") or "UNKNOWN").upper()
    validated = gate.get("validated_sectors") or []
    validated_set = {str(value) for value in validated if value}
    missing_required = [sector for sector in required_sectors if sector not in validated_set]

    if gate_status == "PASS" and gate_mode == "REAL_LOCAL" and not missing_required:
        return "PROTECTED", "", [], gate_mode

    if strict_claim:
        if gate_status != "PASS":
            return "FAIL_CLOSED", f"mechanical_ethics_gate_status_{gate_status.lower()}", missing_required, gate_mode
        if gate_mode != "REAL_LOCAL":
            return "FAIL_CLOSED", f"mechanical_ethics_gate_mode_{gate_mode.lower()}", missing_required, gate_mode
        return "FAIL_CLOSED", "required_sectors_not_validated", missing_required, gate_mode

    if gate_status == "PASS" and gate_mode == "REAL_LOCAL" and missing_required:
        return "NOT_REQUIRED_FOR_CURRENT_CLAIM", "required_sectors_not_validated", missing_required, gate_mode

    if gate_status != "PASS":
        return "NOT_REQUIRED_FOR_CURRENT_CLAIM", f"mechanical_ethics_gate_status_{gate_status.lower()}", missing_required, gate_mode

    return "NOT_REQUIRED_FOR_CURRENT_CLAIM", f"mechanical_ethics_gate_mode_{gate_mode.lower()}", missing_required, gate_mode


def main() -> int:
    parser = argparse.ArgumentParser(description="Write PQ runtime secret protection artifact")
    parser.add_argument("--root", default=".", help="Repository root")
    parser.add_argument(
        "--output",
        default="results/pq_runtime_secret_protection.json",
        help="Output artifact path (relative to --root unless absolute)",
    )
    parser.add_argument(
        "--gate-path",
        default="results/mechanical_ethics_gate.json",
        help="Mechanical ethics gate artifact path (relative to --root unless absolute)",
    )
    parser.add_argument("--claim-level", default="ci_grade", help="Claim level for this execution context")
    parser.add_argument("--runtime-scope", default="canonical_ci_runtime", help="Runtime scope label")
    parser.add_argument("--protector", default="MLKEM768Protector", help="Runtime secret protector identifier")
    parser.add_argument(
        "--policy-version",
        default="CONSTITUTIONAL_CLOSURE_ADDENDUM_V2",
        help="Policy/version label bound to this artifact",
    )
    parser.add_argument(
        "--required-sectors",
        default=DEFAULT_REQUIRED_SECTORS,
        help="Comma-separated required sectors",
    )
    parser.add_argument(
        "--strict-claim-levels",
        default=DEFAULT_STRICT_CLAIM_LEVELS,
        help="Comma-separated claim levels that should fail-closed if protection is not PROTECTED",
    )
    parser.add_argument(
        "--enforce",
        action="store_true",
        help="Return non-zero when strict claim level is not PROTECTED",
    )
    args = parser.parse_args()

    root = Path(args.root).resolve()
    out_path = Path(args.output)
    if not out_path.is_absolute():
        out_path = (root / out_path).resolve()
    gate_path = Path(args.gate_path)
    if not gate_path.is_absolute():
        gate_path = (root / gate_path).resolve()

    required_sectors = parse_csv(args.required_sectors)
    strict_claim_levels = set(parse_csv(args.strict_claim_levels))
    gate = read_json(gate_path)
    gate_rel = to_repo_relative(root, gate_path)

    status, failure_reason, missing_required, gate_mode = build_status(
        gate,
        claim_level=args.claim_level,
        strict_claim_levels=strict_claim_levels,
        required_sectors=required_sectors,
    )

    gate_status = "MISSING" if gate is None else str(gate.get("status") or "UNKNOWN")
    validated_sectors = [] if gate is None else list(gate.get("validated_sectors") or [])
    claim_level_ceiling = "UNKNOWN" if gate is None else str(gate.get("claim_level_ceiling") or "UNKNOWN")

    secret_material = {
        "protector": args.protector,
        "claim_level": args.claim_level,
        "runtime_scope": args.runtime_scope,
        "gate_status": gate_status,
        "gate_mode": gate_mode,
        "missing_required_sectors": missing_required,
        "policy_version": args.policy_version,
    }
    secret_reference = f"pqref:sha256:{stable_hash(secret_material)}"

    payload: dict[str, Any] = {
        "artifactType": "pq_runtime_secret_protection",
        "schemaVersion": "1.0.0",
        "generatedAt": now_utc_iso(),
        "status": status,
        "protector": args.protector,
        "claim_level": args.claim_level,
        "runtime_scope": args.runtime_scope,
        "secret_reference": secret_reference,
        "evidence_ref": gate_rel,
        "policy_version": args.policy_version,
        "gate": {
            "path": gate_rel,
            "status": gate_status,
            "mode": gate_mode,
            "claim_level_ceiling": claim_level_ceiling,
            "validated_sectors": validated_sectors,
            "required_sectors": required_sectors,
            "missing_required_sectors": missing_required,
        },
    }
    if failure_reason:
        payload["failure_reason"] = failure_reason

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(str(out_path))
    print(f"status={status}")

    strict_claim = args.claim_level in strict_claim_levels
    if args.enforce and strict_claim and status != "PROTECTED":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
