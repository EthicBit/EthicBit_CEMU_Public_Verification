# scripts/swarm/case_003/cemu_case_003_anchor_prepare.py
# ETHICBIT / CEMU – CASE 003
# Anchor Preparation Bridge
# Aligned with Authority_Matrix.case_003.md v1.1
# Inputs:
#   - canonical_root.case_003.json
# Outputs:
#   - anchor_prepare.case_003.canonical.json
#   - anchor_receipt.case_003.canonical.json
#   - anchor_verification.case_003.canonical.json

from __future__ import annotations

import json
import hashlib
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict


CASE_ID = "case_003"
BASE_DIR = Path(__file__).resolve().parents[3]
ARTIFACTS_DIR = BASE_DIR / "artifacts" / "cases" / CASE_ID
ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)

CANONICAL_ROOT_FILE = ARTIFACTS_DIR / "canonical_root.case_003.json"


DECISION_MODES = {
    "HUMAN_REQUIRED",
    "HUMAN_SUPERVISED",
    "AUTONOMOUS_WITH_AUDIT",
    "AUTONOMOUS_BLOCK_ONLY",
    "AUTONOMOUS_NOT_ALLOWED",
}

ANCHOR_STATUSES = {
    "PREPARED_PENDING_EXECUTION",
    "EXECUTED_PENDING_RECEIPT",
    "RECEIPT_ATTACHED",
    "VERIFIED",
    "FAILED",
}

NETWORKS = {
    "sepolia",
    "ethereum",
}

HASH_ALGORITHMS = {
    "SHA-256",
}

SIGNATURE_ALGORITHMS = {
    "ECDSA/secp256k1",
}


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def canonicalize_json(payload: Dict[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def sha256_hex(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def stable_json_hash(payload: Dict[str, Any]) -> str:
    return sha256_hex(canonicalize_json(payload))


def read_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def write_json(filename: str, payload: Dict[str, Any]) -> Path:
    path = ARTIFACTS_DIR / filename
    with path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)
    return path


@dataclass
class AuthorityRule:
    operation: str
    decision_mode: str
    authority: str
    escalation_required: bool
    notes: str = ""

    def validate(self) -> None:
        if self.decision_mode not in DECISION_MODES:
            raise ValueError(f"Invalid decision_mode: {self.decision_mode}")


def build_default_authority_rules() -> Dict[str, AuthorityRule]:
    rules = {
        "anchor_prepare": AuthorityRule(
            operation="anchor_prepare",
            decision_mode="HUMAN_SUPERVISED",
            authority="Anchor Preparation Bridge",
            escalation_required=True,
            notes="Anchor preparation is closure-adjacent and must remain supervised.",
        ),
        "anchor_receipt": AuthorityRule(
            operation="anchor_receipt",
            decision_mode="AUTONOMOUS_WITH_AUDIT",
            authority="Anchor Receipt Framework",
            escalation_required=False,
            notes="Receipt attachment may be automatic after confirmed transaction and traceability checks.",
        ),
        "anchor_verification": AuthorityRule(
            operation="anchor_verification",
            decision_mode="AUTONOMOUS_WITH_AUDIT",
            authority="External Anchor Verification Logic",
            escalation_required=False,
            notes="Verification may be automatic if onchain event matching is reproducible.",
        ),
    }
    for rule in rules.values():
        rule.validate()
    return rules


@dataclass
class CanonicalRootInput:
    root_id: str
    root_hash: str
    root_payload_hash: str
    root_status: str
    anchor_ready: bool
    signature_ready: bool
    source_case_bundle_id: str
    source_manifest_id: str
    source_collective_pack_id: str
    decision_mode: str
    authority: str
    escalation_required: bool
    canonical_hash: str

    @classmethod
    def from_artifact(cls, payload: Dict[str, Any]) -> "CanonicalRootInput":
        return cls(
            root_id=payload["root_id"],
            root_hash=payload["root_hash"],
            root_payload_hash=payload["root_payload_hash"],
            root_status=payload["root_status"],
            anchor_ready=payload["anchor_ready"],
            signature_ready=payload["signature_ready"],
            source_case_bundle_id=payload["source_case_bundle_id"],
            source_manifest_id=payload["source_manifest_id"],
            source_collective_pack_id=payload["source_collective_pack_id"],
            decision_mode=payload["decision_mode"],
            authority=payload["authority"],
            escalation_required=payload["escalation_required"],
            canonical_hash=payload["canonical_hash"],
        )


@dataclass
class AnchorPrepareRecord:
    case_id: str
    anchor_prepare_id: str
    network: str
    contract_name: str
    contract_script: str
    verify_script: str
    root_id: str
    root_hash: str
    root_payload_hash: str
    anchor_payload_hash: str
    signature_algorithm: str
    hash_algorithm: str
    anchor_status: str
    ready_for_anchor_execution: bool
    source_case_bundle_id: str
    source_manifest_id: str
    source_collective_pack_id: str
    decision_mode: str
    authority: str
    escalation_required: bool
    generated_at: str

    def validate(self) -> None:
        if self.network not in NETWORKS:
            raise ValueError(f"Invalid network: {self.network}")
        if self.hash_algorithm not in HASH_ALGORITHMS:
            raise ValueError(f"Invalid hash_algorithm: {self.hash_algorithm}")
        if self.signature_algorithm not in SIGNATURE_ALGORITHMS:
            raise ValueError(f"Invalid signature_algorithm: {self.signature_algorithm}")
        if self.anchor_status not in ANCHOR_STATUSES:
            raise ValueError(f"Invalid anchor_status: {self.anchor_status}")


class AnchorPrepareBridge:
    def __init__(self, authority_rules: Dict[str, AuthorityRule]) -> None:
        self.authority_rules = authority_rules

    def load_root(self) -> CanonicalRootInput:
        root_payload = read_json(CANONICAL_ROOT_FILE)
        return CanonicalRootInput.from_artifact(root_payload)

    def build_anchor_payload(self, root: CanonicalRootInput) -> Dict[str, Any]:
        return {
            "case_id": CASE_ID,
            "anchor_scope": {
                "root_id": root.root_id,
                "source_case_bundle_id": root.source_case_bundle_id,
                "source_manifest_id": root.source_manifest_id,
                "source_collective_pack_id": root.source_collective_pack_id,
            },
            "anchor_input": {
                "root_hash": root.root_hash,
                "root_payload_hash": root.root_payload_hash,
                "root_canonical_hash": root.canonical_hash,
            },
            "network_target": "sepolia",
            "contract_target": "ClosureAnchor.sol",
            "execution_bridge": {
                "anchor_script": "scripts/anchor_closure.js",
                "verify_script": "verify_closure_anchor_event.js",
            },
            "prepared_at": now_iso(),
        }

    def build_anchor_prepare_record(
        self,
        root: CanonicalRootInput,
        anchor_payload: Dict[str, Any],
    ) -> Dict[str, Any]:
        rule = self.authority_rules["anchor_prepare"]

        anchor_payload_hash = stable_json_hash(anchor_payload)

        record = AnchorPrepareRecord(
            case_id=CASE_ID,
            anchor_prepare_id=f"{CASE_ID}-ANCHOR-PREP-001",
            network="sepolia",
            contract_name="ClosureAnchor.sol",
            contract_script="scripts/anchor_closure.js",
            verify_script="verify_closure_anchor_event.js",
            root_id=root.root_id,
            root_hash=root.root_hash,
            root_payload_hash=root.root_payload_hash,
            anchor_payload_hash=anchor_payload_hash,
            signature_algorithm="ECDSA/secp256k1",
            hash_algorithm="SHA-256",
            anchor_status="PREPARED_PENDING_EXECUTION",
            ready_for_anchor_execution=(root.anchor_ready and root.signature_ready),
            source_case_bundle_id=root.source_case_bundle_id,
            source_manifest_id=root.source_manifest_id,
            source_collective_pack_id=root.source_collective_pack_id,
            decision_mode=rule.decision_mode,
            authority=rule.authority,
            escalation_required=rule.escalation_required,
            generated_at=now_iso(),
        )
        record.validate()

        payload = {
            **asdict(record),
            "anchor_payload": anchor_payload,
        }
        payload["canonical_hash"] = stable_json_hash(payload)
        return payload

    def build_anchor_receipt_scaffold(
        self,
        root: CanonicalRootInput,
        anchor_prepare_payload: Dict[str, Any],
    ) -> Dict[str, Any]:
        rule = self.authority_rules["anchor_receipt"]

        payload = {
            "case_id": CASE_ID,
            "receipt_id": f"{CASE_ID}-ANCHOR-RECEIPT-001",
            "network": "sepolia",
            "receipt_status": "PREPARED_PENDING_EXECUTION",
            "root_id": root.root_id,
            "root_hash": root.root_hash,
            "root_payload_hash": root.root_payload_hash,
            "anchor_prepare_id": anchor_prepare_payload["anchor_prepare_id"],
            "contract_name": "ClosureAnchor.sol",
            "contract_script": "scripts/anchor_closure.js",
            "tx_hash": None,
            "block_number": None,
            "block_hash": None,
            "contract_address": None,
            "decision_mode": rule.decision_mode,
            "authority": rule.authority,
            "generated_at": now_iso(),
        }
        payload["canonical_hash"] = stable_json_hash(payload)
        return payload

    def build_anchor_verification_scaffold(
        self,
        root: CanonicalRootInput,
        anchor_prepare_payload: Dict[str, Any],
    ) -> Dict[str, Any]:
        rule = self.authority_rules["anchor_verification"]

        payload = {
            "case_id": CASE_ID,
            "verification_id": f"{CASE_ID}-ANCHOR-VERIFY-001",
            "verification_status": "PREPARED_PENDING_EXECUTION",
            "root_id": root.root_id,
            "expected_root_hash": root.root_hash,
            "expected_root_payload_hash": root.root_payload_hash,
            "anchor_prepare_id": anchor_prepare_payload["anchor_prepare_id"],
            "verify_script": "verify_closure_anchor_event.js",
            "verified": False,
            "event_match": None,
            "contract_match": None,
            "root_match": None,
            "tx_hash": None,
            "decision_mode": rule.decision_mode,
            "authority": rule.authority,
            "generated_at": now_iso(),
        }
        payload["canonical_hash"] = stable_json_hash(payload)
        return payload

    def export(
        self,
        anchor_prepare_payload: Dict[str, Any],
        anchor_receipt_payload: Dict[str, Any],
        anchor_verification_payload: Dict[str, Any],
    ) -> None:
        write_json("anchor_prepare.case_003.canonical.json", anchor_prepare_payload)
        write_json("anchor_receipt.case_003.canonical.json", anchor_receipt_payload)
        write_json("anchor_verification.case_003.canonical.json", anchor_verification_payload)


def main() -> None:
    rules = build_default_authority_rules()
    bridge = AnchorPrepareBridge(authority_rules=rules)

    root = bridge.load_root()
    anchor_payload = bridge.build_anchor_payload(root)
    anchor_prepare_payload = bridge.build_anchor_prepare_record(root, anchor_payload)
    anchor_receipt_payload = bridge.build_anchor_receipt_scaffold(root, anchor_prepare_payload)
    anchor_verification_payload = bridge.build_anchor_verification_scaffold(root, anchor_prepare_payload)

    bridge.export(
        anchor_prepare_payload=anchor_prepare_payload,
        anchor_receipt_payload=anchor_receipt_payload,
        anchor_verification_payload=anchor_verification_payload,
    )

    print("=" * 88)
    print("ETHICBIT / CEMU – CASE 003 ANCHOR PREPARE")
    print("=" * 88)
    print(f"Case ID:                {CASE_ID}")
    print(f"Root ID:                {root.root_id}")
    print(f"Root Hash:              {root.root_hash}")
    print("-" * 88)
    print(f"Anchor Prepare ID:      {anchor_prepare_payload['anchor_prepare_id']}")
    print(f"Network:                {anchor_prepare_payload['network']}")
    print(f"Contract:               {anchor_prepare_payload['contract_name']}")
    print(f"Anchor Ready:           {anchor_prepare_payload['ready_for_anchor_execution']}")
    print(f"Anchor Status:          {anchor_prepare_payload['anchor_status']}")
    print("-" * 88)
    print("Artifacts written:")
    print(" - anchor_prepare.case_003.canonical.json")
    print(" - anchor_receipt.case_003.canonical.json")
    print(" - anchor_verification.case_003.canonical.json")
    print("=" * 88)


if __name__ == "__main__":
    main()
