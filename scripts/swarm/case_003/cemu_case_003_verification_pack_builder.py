# scripts/swarm/case_003/cemu_case_003_verification_pack_builder.py
# ETHICBIT / CEMU – CASE 003
# Verification Pack Builder (Fail-Closed Remediated / Compatible)

from __future__ import annotations

import json
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict


CASE_ID = "case_003"
BASE_DIR = Path(__file__).resolve().parents[3]
ARTIFACTS_DIR = BASE_DIR / "artifacts" / "cases" / CASE_ID
ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)

CANONICAL_ROOT_FILE = ARTIFACTS_DIR / "canonical_root.case_003.json"
ANCHOR_PREPARE_FILE = ARTIFACTS_DIR / "anchor_prepare.case_003.canonical.json"
ANCHOR_RECEIPT_FILE = ARTIFACTS_DIR / "anchor_receipt.case_003.canonical.json"
ANCHOR_VERIFICATION_FILE = ARTIFACTS_DIR / "anchor_verification.case_003.canonical.json"
ARTIFACT_MANIFEST_FILE = ARTIFACTS_DIR / "artifact_manifest.case_003.canonical.json"
CASE_BUNDLE_FILE = ARTIFACTS_DIR / "case_bundle.case_003.canonical.json"

PACKAGE_LOCK_FILE = BASE_DIR / "package-lock.json"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path: Path, payload: Dict[str, Any]) -> None:
    with path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)


def stable_hash(payload: Dict[str, Any]) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def normalize_hex_32(value: str) -> str:
    v = (value or "").strip().lower()
    if not v:
        return v
    if not v.startswith("0x"):
        v = "0x" + v
    return v


def get_case_bundle_id(case_bundle: Dict[str, Any]) -> str:
    return (
        case_bundle.get("bundle_id")
        or case_bundle.get("case_bundle_id")
        or case_bundle.get("bundle", {}).get("bundle_id")
        or f"{CASE_ID}-BUNDLE-001"
    )


def get_case_bundle_status(case_bundle: Dict[str, Any]) -> str:
    return (
        case_bundle.get("bundle_status")
        or case_bundle.get("status")
        or case_bundle.get("bundle", {}).get("bundle_status")
        or "UNKNOWN"
    )


def build_environment() -> Dict[str, Any]:
    payload = {
        "case_id": CASE_ID,
        "environment_id": f"{CASE_ID}-VERIFICATION-ENV-001",
        "container_hash": "23a16bdc30c62166a-placeholder",
        "runtime_version": "python-3.12",
        "dependency_lock": "LOCKFILE_PRESENT" if PACKAGE_LOCK_FILE.exists() else "LOCKFILE_MISSING",
        "seed": f"{CASE_ID}-REPLAY-SEED-001",
        "generated_at": now_iso(),
    }
    payload["canonical_hash"] = stable_hash(payload)
    return payload


def main() -> None:
    canonical_root = read_json(CANONICAL_ROOT_FILE)
    anchor_prepare = read_json(ANCHOR_PREPARE_FILE)
    anchor_receipt = read_json(ANCHOR_RECEIPT_FILE)
    anchor_verification = read_json(ANCHOR_VERIFICATION_FILE)
    artifact_manifest = read_json(ARTIFACT_MANIFEST_FILE)
    case_bundle = read_json(CASE_BUNDLE_FILE)

    verification_environment = build_environment()

    normalized_root_hash = normalize_hex_32(canonical_root.get("root_hash", ""))
    normalized_expected_root_hash = normalize_hex_32(anchor_verification.get("expected_root_hash", ""))

    expected_root_hash_match = normalized_root_hash == normalized_expected_root_hash
    if expected_root_hash_match is not True:
        raise RuntimeError("FAIL_CLOSED: expected_root_hash_match is not true")
    verified = bool(anchor_verification.get("verified", False))
    event_match = bool(anchor_verification.get("event_match", False))
    contract_match = bool(anchor_verification.get("contract_match", False))
    root_match = bool(anchor_verification.get("root_match", False))

    critical_ok = all([
        verified is True,
        event_match is True,
        contract_match is True,
        root_match is True,
        expected_root_hash_match is True,
    ])

    if critical_ok:
        verification_status = "VERIFIED_REPRODUCIBLE"
        fail_closed_reason = "None"
    else:
        verification_status = "VERIFICATION_FAILED"
        fail_closed_reason = "Critical anchor/root verification assertion failed."

    verification_pack = {
        "case_id": CASE_ID,
        "verification_pack_id": f"{CASE_ID}-VERIFICATION-PACK-001",
        "verification_status": verification_status,
        "verification_scope": {
            "root_id": canonical_root.get("root_id", f"{CASE_ID}-ROOT-001"),
            "manifest_id": artifact_manifest.get("manifest_id", f"{CASE_ID}-MANIFEST-001"),
            "case_bundle_id": get_case_bundle_id(case_bundle),
            "anchor_prepare_id": anchor_prepare.get("anchor_prepare_id", f"{CASE_ID}-ANCHOR-PREP-001"),
            "anchor_receipt_id": anchor_receipt.get("receipt_id", f"{CASE_ID}-ANCHOR-RECEIPT-001"),
            "anchor_verification_id": anchor_verification.get("verification_id", f"{CASE_ID}-ANCHOR-VERIFY-001"),
        },
        "reproducibility": {
            "environment_id": verification_environment["environment_id"],
            "container_hash": verification_environment["container_hash"],
            "runtime_version": verification_environment["runtime_version"],
            "dependency_lock": verification_environment["dependency_lock"],
            "seed": verification_environment["seed"],
        },
        "expected_hashes": {
            "canonical_root_hash": canonical_root.get("canonical_hash"),
            "anchor_prepare_hash": anchor_prepare.get("canonical_hash"),
            "anchor_receipt_hash": anchor_receipt.get("canonical_hash"),
            "anchor_verification_hash": anchor_verification.get("canonical_hash"),
            "artifact_manifest_hash": artifact_manifest.get("canonical_hash"),
            "case_bundle_hash": case_bundle.get("canonical_hash"),
        },
        "verification_assertions": {
            "root_status": canonical_root.get("root_status"),
            "receipt_status": anchor_receipt.get("receipt_status"),
            "anchor_verification_status": anchor_verification.get("verification_status"),
            "expected_root_hash_match": expected_root_hash_match,
            "verified": verified,
            "event_match": event_match,
            "contract_match": contract_match,
            "root_match": root_match,
            "bundle_status": get_case_bundle_status(case_bundle),
        },
        "fail_closed_reason": fail_closed_reason,
        "decision_mode": "HUMAN_SUPERVISED",
        "authority": "Verification Pack Builder",
        "escalation_required": True,
        "generated_at": now_iso(),
    }

    verification_pack["canonical_hash"] = stable_hash(verification_pack)

    write_json(ARTIFACTS_DIR / "verification_environment.case_003.canonical.json", verification_environment)
    write_json(ARTIFACTS_DIR / "verification_pack.case_003.canonical.json", verification_pack)

    print("=" * 88)
    print("ETHICBIT / CEMU – CASE 003 VERIFICATION PACK BUILDER")
    print("=" * 88)
    print(f"Case ID:                {CASE_ID}")
    print(f"Root ID:                {verification_pack['verification_scope']['root_id']}")
    print(f"Manifest ID:            {verification_pack['verification_scope']['manifest_id']}")
    print(f"Case Bundle ID:         {verification_pack['verification_scope']['case_bundle_id']}")
    print("-" * 88)
    print(f"Environment ID:         {verification_environment['environment_id']}")
    print(f"Verification Pack ID:   {verification_pack['verification_pack_id']}")
    print(f"Verification Status:    {verification_pack['verification_status']}")
    print(f"Dependency Lock:        {verification_pack['reproducibility']['dependency_lock']}")
    print(f"Fail-Closed Reason:     {verification_pack['fail_closed_reason']}")
    print("-" * 88)
    print("Artifacts written:")
    print(" - verification_environment.case_003.canonical.json")
    print(" - verification_pack.case_003.canonical.json")
    print("=" * 88)


if __name__ == "__main__":
    main()