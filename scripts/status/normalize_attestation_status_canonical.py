#!/usr/bin/env python3
"""Build canonical attestation status artifact for readiness gating.

This script normalizes heterogeneous attestation states into a single canonical
artifact consumed by run_production_readiness.sh.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA_ID = "ETHICBIT_ATTESTATION_STATUS_CANONICAL_V1"
VERSION = "1.0.0"
POLICY_VERSION = "attestation-normalization-policy.v1.0.0"

FINAL_EQUIVALENT_STATUSES = {
    "PASS_SLSA_FINAL",
    "VERIFIED_REPRODUCIBLE",
    "VERIFIED",
}
FINAL_EQUIVALENT_BASIS = {
    "operative_attestation_plus_reproducibility",
    "slsa_l4_final",
    "reproducible_attested_closure",
}


def now_utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def read_json(path: Path) -> Any:
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        while True:
            chunk = handle.read(65536)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def _upper(value: Any) -> str:
    return str(value or "").strip().upper()


def derive_slsa_equivalence(slsa_final: dict[str, Any]) -> tuple[bool, str, str]:
    status = _upper(slsa_final.get("status"))
    basis = str(slsa_final.get("basis") or "").strip()
    basis_lc = basis.lower()

    if status in FINAL_EQUIVALENT_STATUSES and (not basis or basis_lc in FINAL_EQUIVALENT_BASIS):
        return True, status, basis
    return False, status, basis


def normalize_step(
    *,
    step_name: str,
    statement_ref: str,
    statement_payload: dict[str, Any] | None,
    attestation_index_status: str,
    slsa_equivalent: bool,
    slsa_status: str,
) -> dict[str, Any]:
    statement_status = _upper((statement_payload or {}).get("status"))
    verification_status = _upper((statement_payload or {}).get("verificationStatus"))

    normalized = "ATTESTATION_NOT_VERIFIED"
    reason = "NO_ACCEPTED_PROOF"

    if verification_status == "VERIFIED" or statement_status in {"VERIFIED", "ATTESTATION_VERIFIED"}:
        normalized = "ATTESTATION_VERIFIED"
        reason = "IN_TOTO_STATEMENT_VERIFIED"
    elif slsa_equivalent:
        normalized = "ATTESTATION_VERIFIED_EQUIVALENT"
        reason = f"SLSA_FINAL_EQUIVALENT:{slsa_status}"

    readiness_accepted = normalized in {"ATTESTATION_VERIFIED", "ATTESTATION_VERIFIED_EQUIVALENT"}

    return {
        "step": step_name,
        "required": True,
        "statementRef": statement_ref,
        "attestationIndexStatus": attestation_index_status,
        "statementStatus": statement_status,
        "statementVerificationStatus": verification_status,
        "normalizedStatus": normalized,
        "normalizationReason": reason,
        "readinessAccepted": readiness_accepted,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Normalize attestation states into canonical readiness artifact")
    parser.add_argument("--root", default=".", help="Repository root")
    parser.add_argument("--strict", action="store_true", help="Exit with code 2 if canonical gate is not PASS")
    args = parser.parse_args()

    root = Path(args.root).resolve()

    in_toto_index_path = root / "assurance/in-toto/attestation-index.json"
    slsa_final_path = root / "attestations/slsa_l4_final_attestation.json"
    slsa_operative_path = root / "attestations/slsa_l4_operative_attestation.json"
    output_path = root / "artifacts/history/swarm/attestation_status.canonical.json"

    if not in_toto_index_path.exists():
        raise SystemExit(f"ATT_STATUS_INVALID: missing {in_toto_index_path}")
    if not slsa_final_path.exists():
        raise SystemExit(f"ATT_STATUS_INVALID: missing {slsa_final_path}")

    in_toto_index = read_json(in_toto_index_path)
    if not isinstance(in_toto_index, dict):
        raise SystemExit("ATT_STATUS_INVALID: in-toto index must be a JSON object")

    slsa_final = read_json(slsa_final_path)
    if not isinstance(slsa_final, dict):
        raise SystemExit("ATT_STATUS_INVALID: slsa final attestation must be a JSON object")

    slsa_operative: dict[str, Any] | None = None
    if slsa_operative_path.exists():
        payload = read_json(slsa_operative_path)
        if isinstance(payload, dict):
            slsa_operative = payload

    slsa_equivalent, slsa_status, slsa_basis = derive_slsa_equivalence(slsa_final)

    attestations = in_toto_index.get("attestations")
    if not isinstance(attestations, list):
        raise SystemExit("ATT_STATUS_INVALID: attestation-index.attestations must be an array")

    steps: list[dict[str, Any]] = []
    for entry in attestations:
        if not isinstance(entry, dict):
            continue
        step_name = str(entry.get("step") or "").strip()
        statement_ref = str(entry.get("statement_ref") or "").strip()
        index_status = _upper(entry.get("status"))
        if not step_name:
            continue

        statement_payload: dict[str, Any] | None = None
        if statement_ref:
            statement_path = root / statement_ref
            if statement_path.exists():
                payload = read_json(statement_path)
                if isinstance(payload, dict):
                    statement_payload = payload

        step = normalize_step(
            step_name=step_name,
            statement_ref=statement_ref,
            statement_payload=statement_payload,
            attestation_index_status=index_status,
            slsa_equivalent=slsa_equivalent,
            slsa_status=slsa_status,
        )
        steps.append(step)

    required_steps = [step for step in steps if step.get("required") is True]
    accepted_steps = [step for step in required_steps if step.get("readinessAccepted") is True]

    gate_status = "PASS" if required_steps and len(accepted_steps) == len(required_steps) else "FAIL"
    gate_reason = "ALL_REQUIRED_STEPS_ACCEPTED" if gate_status == "PASS" else "REQUIRED_STEPS_NOT_ACCEPTED"

    canonical_status = "VERIFIED" if gate_status == "PASS" else "NOT_VERIFIED"

    source_hashes: dict[str, str] = {
        "inTotoIndex": sha256_file(in_toto_index_path),
        "slsaFinal": sha256_file(slsa_final_path),
    }
    if slsa_operative_path.exists():
        source_hashes["slsaOperative"] = sha256_file(slsa_operative_path)

    payload = {
        "schema_id": SCHEMA_ID,
        "version": VERSION,
        "status": canonical_status,
        "policyVersion": POLICY_VERSION,
        "generatedAt": now_utc_iso(),
        "equivalenceModel": {
            "acceptedCanonicalStatus": "ATTESTATION_VERIFIED",
            "acceptedEquivalentStatus": "ATTESTATION_VERIFIED_EQUIVALENT",
            "slsaFinalEquivalentStatuses": sorted(FINAL_EQUIVALENT_STATUSES),
            "slsaFinalEquivalentBasis": sorted(FINAL_EQUIVALENT_BASIS),
        },
        "sources": {
            "inTotoIndex": str(in_toto_index_path),
            "slsaFinal": str(slsa_final_path),
            "slsaOperative": str(slsa_operative_path),
            "output": str(output_path),
        },
        "sourceHashes": source_hashes,
        "slsaAssessment": {
            "equivalent": slsa_equivalent,
            "status": slsa_status,
            "basis": slsa_basis,
        },
        "requiredStepsEvaluated": len(required_steps),
        "requiredStepsAccepted": len(accepted_steps),
        "steps": steps,
        "gate": {
            "status": gate_status,
            "reason": gate_reason,
        },
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(payload["status"])
    print(f"DETAIL: gate={gate_status}; accepted={len(accepted_steps)}/{len(required_steps)}; output={output_path}")

    if args.strict and gate_status != "PASS":
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
