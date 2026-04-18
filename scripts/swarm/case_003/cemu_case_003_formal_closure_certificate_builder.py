# scripts/swarm/case_003/cemu_case_003_formal_closure_certificate_builder.py
# ETHICBIT / CEMU – CASE 003
# Formal Closure Certificate Builder (Human Approval Remediated)

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

CLOSURE_STATE_FILE = ARTIFACTS_DIR / "closure_state.case_003.canonical.json"
PRE_SEALING_FILE = ARTIFACTS_DIR / "pre_sealing_record.case_003.canonical.json"
VERIFICATION_PACK_FILE = ARTIFACTS_DIR / "verification_pack.case_003.canonical.json"
CANONICAL_ROOT_FILE = ARTIFACTS_DIR / "canonical_root.case_003.json"
ARTIFACT_MANIFEST_FILE = ARTIFACTS_DIR / "artifact_manifest.case_003.canonical.json"
HUMAN_APPROVAL_FILE = ARTIFACTS_DIR / "human_approval.case_003.canonical.json"


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


def main() -> None:
    closure_state = read_json(CLOSURE_STATE_FILE)
    pre_sealing = read_json(PRE_SEALING_FILE)
    verification_pack = read_json(VERIFICATION_PACK_FILE)
    canonical_root = read_json(CANONICAL_ROOT_FILE)
    artifact_manifest = read_json(ARTIFACT_MANIFEST_FILE)
    human_approval = read_json(HUMAN_APPROVAL_FILE)

    approval_ok = human_approval.get("approval_status") == "APPROVED"
    closure_state_ok = closure_state.get("closure_state") == "FORMALLY_FROZEN"
    verification_ok = verification_pack.get("verification_status") == "VERIFIED_REPRODUCIBLE"
    eligibility_ok = closure_state.get("certificate_eligibility") is True

    if closure_state_ok and verification_ok and eligibility_ok and approval_ok:
        certificate_status = "PENDING_HUMAN_APPROVAL"
    else:
        certificate_status = "NOT_ELIGIBLE"

    payload = {
        "case_id": CASE_ID,
        "certificate_id": f"{CASE_ID}-FORMAL-CLOSURE-CERT-001",
        "certificate_status": certificate_status,
        "closure_state_id": closure_state.get("closure_state_id", f"{CASE_ID}-CLOSURE-STATE-001"),
        "closure_state": closure_state.get("closure_state"),
        "closure_reason": closure_state.get("closure_reason"),
        "closure_reason_code": closure_state.get("closure_reason_code"),
        "pre_sealing_id": pre_sealing.get("pre_sealing_id", f"{CASE_ID}-PRE-SEAL-001"),
        "pre_seal_status": pre_sealing.get("pre_seal_status"),
        "critical_state": pre_sealing.get("critical_state", "HIGH_CRITICALITY_PRE_SEALABLE"),
        "verification_pack_id": verification_pack.get("verification_pack_id", f"{CASE_ID}-VERIFICATION-PACK-001"),
        "verification_status": verification_pack.get("verification_status"),
        "root_id": canonical_root.get("root_id", f"{CASE_ID}-ROOT-001"),
        "root_hash": canonical_root.get("root_hash"),
        "root_payload_hash": canonical_root.get("root_payload_hash"),
        "manifest_id": artifact_manifest.get("manifest_id", f"{CASE_ID}-MANIFEST-001"),
        "decision_mode": "HUMAN_REQUIRED",
        "authority": "Formal Closure Registry",
        "escalation_required": True,
        "human_approval_id": human_approval.get("approval_id"),
        "human_approval_status": human_approval.get("approval_status"),
        "issued_at": now_iso(),
        "linked_hashes": {
            "closure_state_hash": closure_state.get("canonical_hash"),
            "pre_sealing_hash": pre_sealing.get("canonical_hash"),
            "verification_pack_hash": verification_pack.get("canonical_hash"),
            "canonical_root_hash": canonical_root.get("canonical_hash"),
            "artifact_manifest_hash": artifact_manifest.get("canonical_hash"),
            "human_approval_hash": stable_hash(human_approval),
        },
    }

    payload["canonical_hash"] = stable_hash(payload)

    write_json(ARTIFACTS_DIR / "formal_closure_certificate.case_003.canonical.json", payload)

    print("=" * 88)
    print("ETHICBIT / CEMU – CASE 003 FORMAL CLOSURE CERTIFICATE BUILDER")
    print("=" * 88)
    print(f"Case ID:                {CASE_ID}")
    print(f"Certificate ID:         {payload['certificate_id']}")
    print(f"Certificate Status:     {payload['certificate_status']}")
    print(f"Closure State:          {payload['closure_state']}")
    print(f"Verification Status:    {payload['verification_status']}")
    print(f"Root ID:                {payload['root_id']}")
    print(f"Human Approval:         {payload['human_approval_status']}")
    print("-" * 88)
    print("Artifacts written:")
    print(" - formal_closure_certificate.case_003.canonical.json")
    print("=" * 88)


if __name__ == "__main__":
    main()