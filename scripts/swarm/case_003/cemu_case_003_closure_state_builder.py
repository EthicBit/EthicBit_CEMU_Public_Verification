# scripts/swarm/case_003/cemu_case_003_closure_state_builder.py
# ETHICBIT / CEMU – CASE 003
# Closure State Builder (Human Approval Remediated)

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

PRE_SEALING_FILE = ARTIFACTS_DIR / "pre_sealing_record.case_003.canonical.json"
ANCHOR_RECEIPT_FILE = ARTIFACTS_DIR / "anchor_receipt.case_003.canonical.json"
ANCHOR_VERIFICATION_FILE = ARTIFACTS_DIR / "anchor_verification.case_003.canonical.json"
VERIFICATION_PACK_FILE = ARTIFACTS_DIR / "verification_pack.case_003.canonical.json"
CANONICAL_ROOT_FILE = ARTIFACTS_DIR / "canonical_root.case_003.json"
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
    pre_sealing = read_json(PRE_SEALING_FILE)
    anchor_receipt = read_json(ANCHOR_RECEIPT_FILE)
    anchor_verification = read_json(ANCHOR_VERIFICATION_FILE)
    verification_pack = read_json(VERIFICATION_PACK_FILE)
    canonical_root = read_json(CANONICAL_ROOT_FILE)
    human_approval = read_json(HUMAN_APPROVAL_FILE)

    approval_ok = human_approval.get("approval_status") == "APPROVED"

    pre_seal_status = pre_sealing.get("pre_seal_status")
    receipt_status = anchor_receipt.get("receipt_status")
    verification_status = anchor_verification.get("verification_status")
    verification_pack_status = verification_pack.get("verification_status")

    if (
        pre_seal_status == "PRE_SEALED_PENDING_FORMAL_CLOSURE"
        and receipt_status == "RECEIPT_ATTACHED"
        and verification_status == "VERIFIED"
        and verification_pack_status == "VERIFIED_REPRODUCIBLE"
        and approval_ok
    ):
        closure_state = "FORMALLY_FROZEN"
        closure_reason = "Human-approved pre-sealed case reached full verification convergence and formal closure."
        closure_reason_code = "CLS_FORMAL_1000"
        certificate_eligibility = True
        anchor_dependency = "SATISFIED"
    elif (
        pre_seal_status == "PRE_SEALED_PENDING_FORMAL_CLOSURE"
        and receipt_status == "RECEIPT_ATTACHED"
        and verification_status == "VERIFIED"
        and verification_pack_status == "VERIFIED_REPRODUCIBLE"
        and not approval_ok
    ):
        closure_state = "PRE_SEALED_PENDING_FORMAL_CLOSURE"
        closure_reason = "Verification converged, but human approval is still required before formal freezing."
        closure_reason_code = "CLS_HUMAN_900"
        certificate_eligibility = False
        anchor_dependency = "SATISFIED"
    elif pre_seal_status == "PRE_SEALED_PENDING_FORMAL_CLOSURE":
        closure_state = "PRE_SEALED_PENDING_FORMAL_CLOSURE"
        closure_reason = "Pre-sealing completed; awaiting final verification convergence."
        closure_reason_code = "CLS_PRESEAL_800"
        certificate_eligibility = False
        anchor_dependency = "PARTIALLY_SATISFIED"
    else:
        closure_state = "FREEZE_EXECUTED_PENDING_EXTERNAL_ANCHOR"
        closure_reason = "Formal closure conditions are not yet satisfied."
        closure_reason_code = "CLS_ANCHOR_600"
        certificate_eligibility = False
        anchor_dependency = "PENDING_EXECUTION"

    payload = {
        "case_id": CASE_ID,
        "closure_state_id": f"{CASE_ID}-CLOSURE-STATE-001",
        "closure_state": closure_state,
        "closure_reason": closure_reason,
        "closure_reason_code": closure_reason_code,
        "pre_sealing_id": pre_sealing.get("pre_sealing_id", f"{CASE_ID}-PRE-SEAL-001"),
        "pre_seal_status": pre_seal_status,
        "receipt_id": anchor_receipt.get("receipt_id", f"{CASE_ID}-ANCHOR-RECEIPT-001"),
        "receipt_status": receipt_status,
        "verification_id": anchor_verification.get("verification_id", f"{CASE_ID}-ANCHOR-VERIFY-001"),
        "verification_status": verification_status,
        "verification_pack_id": verification_pack.get("verification_pack_id", f"{CASE_ID}-VERIFICATION-PACK-001"),
        "root_id": canonical_root.get("root_id", f"{CASE_ID}-ROOT-001"),
        "root_hash": canonical_root.get("root_hash"),
        "certificate_eligibility": certificate_eligibility,
        "anchor_dependency": anchor_dependency,
        "decision_mode": "HUMAN_REQUIRED",
        "authority": "Closure State Machine",
        "escalation_required": True,
        "human_approval_id": human_approval.get("approval_id"),
        "human_approval_status": human_approval.get("approval_status"),
        "generated_at": now_iso(),
    }

    payload["canonical_hash"] = stable_hash(payload)

    write_json(ARTIFACTS_DIR / "closure_state.case_003.canonical.json", payload)

    print("=" * 88)
    print("ETHICBIT / CEMU – CASE 003 CLOSURE STATE BUILDER")
    print("=" * 88)
    print(f"Case ID:                {CASE_ID}")
    print(f"Closure State ID:       {payload['closure_state_id']}")
    print(f"Closure State:          {payload['closure_state']}")
    print(f"Reason Code:            {payload['closure_reason_code']}")
    print(f"Certificate Eligible:   {payload['certificate_eligibility']}")
    print(f"Anchor Dependency:      {payload['anchor_dependency']}")
    print(f"Human Approval:         {payload['human_approval_status']}")
    print("-" * 88)
    print("Artifacts written:")
    print(" - closure_state.case_003.canonical.json")
    print("=" * 88)


if __name__ == "__main__":
    main()