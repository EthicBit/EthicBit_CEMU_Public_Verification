# scripts/swarm/case_003/cemu_case_003_root_builder.py
# ETHICBIT / CEMU – CASE 003
# Canonical Root Builder
# Aligned with Authority_Matrix.case_003.md v1.1
# Inputs:
#   - case_bundle.case_003.canonical.json
#   - artifact_manifest.case_003.canonical.json
#   - collective_pack.case_003.canonical.json
# Outputs:
#   - canonical_root.case_003.json

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

CASE_BUNDLE_FILE = ARTIFACTS_DIR / "case_bundle.case_003.canonical.json"
MANIFEST_FILE = ARTIFACTS_DIR / "artifact_manifest.case_003.canonical.json"
COLLECTIVE_PACK_FILE = ARTIFACTS_DIR / "collective_pack.case_003.canonical.json"


DECISION_MODES = {
    "HUMAN_REQUIRED",
    "HUMAN_SUPERVISED",
    "AUTONOMOUS_WITH_AUDIT",
    "AUTONOMOUS_BLOCK_ONLY",
    "AUTONOMOUS_NOT_ALLOWED",
}

CANONICALIZATION_METHODS = {"JSON_SORTED_COMPACT_UTF8"}
HASH_ALGORITHMS = {"SHA-256"}
SIGNATURE_ALGORITHMS = {"ECDSA/secp256k1"}
ROOT_STATUSES = {
    "SIGNATURE_READY",
    "ANCHOR_READY",
    "PREPARED_PENDING_REVIEW",
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
        "canonical_root_build": AuthorityRule(
            operation="canonical_root_build",
            decision_mode="HUMAN_SUPERVISED",
            authority="Canonical Root Builder",
            escalation_required=True,
            notes="Root generation is closure-adjacent and should remain supervised.",
        ),
    }
    for rule in rules.values():
        rule.validate()
    return rules


@dataclass
class ManifestInput:
    manifest_id: str
    entity_id: str
    action_id: str
    canonical_hash: str

    @classmethod
    def from_artifact(cls, payload: Dict[str, Any]) -> "ManifestInput":
        return cls(
            manifest_id=payload["manifest_id"],
            entity_id=payload["entity_id"],
            action_id=payload["action_id"],
            canonical_hash=payload["canonical_hash"],
        )


@dataclass
class CollectivePackInput:
    collective_pack_id: str
    canonical_hash: str

    @classmethod
    def from_artifact(cls, payload: Dict[str, Any]) -> "CollectivePackInput":
        return cls(
            collective_pack_id=payload["collective_pack_id"],
            canonical_hash=payload["canonical_hash"],
        )


@dataclass
class CaseBundleInput:
    case_bundle_id: str
    bundle_status: str
    residual_state: str
    non_closure_basis: str
    canonical_hash: str
    decision_mode: str

    @classmethod
    def from_artifact(cls, payload: Dict[str, Any]) -> "CaseBundleInput":
        return cls(
            case_bundle_id=payload["case_bundle_id"],
            bundle_status=payload["bundle_status"],
            residual_state=payload["residual_state"],
            non_closure_basis=payload["non_closure_basis"],
            canonical_hash=payload["canonical_hash"],
            decision_mode=payload["decision_mode"],
        )


@dataclass
class CanonicalRootRecord:
    case_id: str
    root_id: str
    root_hash: str
    root_payload_hash: str
    canonicalization_method: str
    hash_algorithm: str
    signature_algorithm: str
    signature_ready: bool
    anchor_ready: bool
    root_status: str
    source_case_bundle_id: str
    source_manifest_id: str
    source_collective_pack_id: str
    decision_mode: str
    authority: str
    escalation_required: bool
    generated_at: str

    def validate(self) -> None:
        if self.canonicalization_method not in CANONICALIZATION_METHODS:
            raise ValueError(f"Invalid canonicalization_method: {self.canonicalization_method}")
        if self.hash_algorithm not in HASH_ALGORITHMS:
            raise ValueError(f"Invalid hash_algorithm: {self.hash_algorithm}")
        if self.signature_algorithm not in SIGNATURE_ALGORITHMS:
            raise ValueError(f"Invalid signature_algorithm: {self.signature_algorithm}")
        if self.root_status not in ROOT_STATUSES:
            raise ValueError(f"Invalid root_status: {self.root_status}")


class CanonicalRootBuilder:
    def __init__(self, authority_rules: Dict[str, AuthorityRule]) -> None:
        self.authority_rules = authority_rules

    def load_inputs(
        self,
    ) -> tuple[ManifestInput, CollectivePackInput, CaseBundleInput]:
        manifest_payload = read_json(MANIFEST_FILE)
        collective_pack_payload = read_json(COLLECTIVE_PACK_FILE)
        case_bundle_payload = read_json(CASE_BUNDLE_FILE)

        return (
            ManifestInput.from_artifact(manifest_payload),
            CollectivePackInput.from_artifact(collective_pack_payload),
            CaseBundleInput.from_artifact(case_bundle_payload),
        )

    def build_root_payload(
        self,
        manifest: ManifestInput,
        collective_pack: CollectivePackInput,
        case_bundle: CaseBundleInput,
    ) -> Dict[str, Any]:
        return {
            "case_id": CASE_ID,
            "root_scope": {
                "case_bundle_id": case_bundle.case_bundle_id,
                "manifest_id": manifest.manifest_id,
                "collective_pack_id": collective_pack.collective_pack_id,
            },
            "canonical_inputs": {
                "case_bundle_hash": case_bundle.canonical_hash,
                "manifest_hash": manifest.canonical_hash,
                "collective_pack_hash": collective_pack.canonical_hash,
            },
            "bundle_status": case_bundle.bundle_status,
            "residual_state": case_bundle.residual_state,
            "non_closure_basis": case_bundle.non_closure_basis,
            "generated_at": now_iso(),
        }

    def build_root_record(
        self,
        manifest: ManifestInput,
        collective_pack: CollectivePackInput,
        case_bundle: CaseBundleInput,
        root_payload: Dict[str, Any],
    ) -> Dict[str, Any]:
        rule = self.authority_rules["canonical_root_build"]

        canonical_payload = canonicalize_json(root_payload)
        root_payload_hash = sha256_hex(canonical_payload)

        root_seed = {
            "case_id": CASE_ID,
            "root_payload_hash": root_payload_hash,
            "case_bundle_hash": case_bundle.canonical_hash,
        }
        root_hash = stable_json_hash(root_seed)

        root_status = "ANCHOR_READY" if case_bundle.bundle_status == "CLOSURE_READY_PENDING_ROOT" else "PREPARED_PENDING_REVIEW"

        record = CanonicalRootRecord(
            case_id=CASE_ID,
            root_id=f"{CASE_ID}-ROOT-001",
            root_hash=root_hash,
            root_payload_hash=root_payload_hash,
            canonicalization_method="JSON_SORTED_COMPACT_UTF8",
            hash_algorithm="SHA-256",
            signature_algorithm="ECDSA/secp256k1",
            signature_ready=True,
            anchor_ready=(root_status == "ANCHOR_READY"),
            root_status=root_status,
            source_case_bundle_id=case_bundle.case_bundle_id,
            source_manifest_id=manifest.manifest_id,
            source_collective_pack_id=collective_pack.collective_pack_id,
            decision_mode=rule.decision_mode,
            authority=rule.authority,
            escalation_required=rule.escalation_required,
            generated_at=now_iso(),
        )
        record.validate()

        payload = {
            **asdict(record),
            "root_payload": root_payload,
        }
        payload["canonical_hash"] = stable_json_hash(payload)
        return payload

    def export(self, payload: Dict[str, Any]) -> None:
        write_json("canonical_root.case_003.json", payload)


def main() -> None:
    rules = build_default_authority_rules()
    builder = CanonicalRootBuilder(authority_rules=rules)

    manifest, collective_pack, case_bundle = builder.load_inputs()

    root_payload = builder.build_root_payload(
        manifest=manifest,
        collective_pack=collective_pack,
        case_bundle=case_bundle,
    )
    root_record = builder.build_root_record(
        manifest=manifest,
        collective_pack=collective_pack,
        case_bundle=case_bundle,
        root_payload=root_payload,
    )

    builder.export(root_record)

    print("=" * 88)
    print("ETHICBIT / CEMU – CASE 003 CANONICAL ROOT BUILDER")
    print("=" * 88)
    print(f"Case ID:                {CASE_ID}")
    print(f"Manifest ID:            {manifest.manifest_id}")
    print(f"Collective Pack ID:     {collective_pack.collective_pack_id}")
    print(f"Case Bundle ID:         {case_bundle.case_bundle_id}")
    print("-" * 88)
    print(f"Root ID:                {root_record['root_id']}")
    print(f"Root Hash:              {root_record['root_hash']}")
    print(f"Root Payload Hash:      {root_record['root_payload_hash']}")
    print(f"Root Status:            {root_record['root_status']}")
    print(f"Anchor Ready:           {root_record['anchor_ready']}")
    print(f"Decision Mode:          {root_record['decision_mode']}")
    print("-" * 88)
    print("Artifacts written:")
    print(" - canonical_root.case_003.json")
    print("=" * 88)


if __name__ == "__main__":
    main()
