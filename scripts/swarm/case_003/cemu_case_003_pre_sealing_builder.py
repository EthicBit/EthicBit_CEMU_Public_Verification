# scripts/swarm/case_003/cemu_case_003_pre_sealing_builder.py
# ETHICBIT / CEMU – CASE 003
# Pre-Sealing Record Builder
# Aligned with Authority_Matrix.case_003.md v1.1
# Inputs:
#   - verification_pack.case_003.canonical.json
#   - swarm_containment_state.case_003.canonical.json
#   - freeze_decision.case_003.canonical.json
#   - canonical_root.case_003.json
# Outputs:
#   - pre_sealing_record.case_003.canonical.json

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

VERIFICATION_PACK_FILE = ARTIFACTS_DIR / "verification_pack.case_003.canonical.json"
SWARM_CONTAINMENT_FILE = ARTIFACTS_DIR / "swarm_containment_state.case_003.canonical.json"
FREEZE_DECISION_FILE = ARTIFACTS_DIR / "freeze_decision.case_003.canonical.json"
CANONICAL_ROOT_FILE = ARTIFACTS_DIR / "canonical_root.case_003.json"


DECISION_MODES = {
    "HUMAN_REQUIRED",
    "HUMAN_SUPERVISED",
    "AUTONOMOUS_WITH_AUDIT",
    "AUTONOMOUS_BLOCK_ONLY",
    "AUTONOMOUS_NOT_ALLOWED",
}

PRE_SEAL_STATUSES = {
    "NOT_REQUIRED",
    "PRE_SEAL_ELIGIBLE",
    "PRE_SEALED_PENDING_FORMAL_CLOSURE",
    "PRE_SEAL_BLOCKED_PENDING_REVIEW",
}

CRITICAL_STATES = {
    "NON_CRITICAL",
    "SENSITIVE",
    "FRONTIER_REINFORCED",
    "HIGH_CRITICALITY_PRE_SEALABLE",
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
        "pre_sealing": AuthorityRule(
            operation="pre_sealing",
            decision_mode="HUMAN_REQUIRED",
            authority="Frontier Pre-Sealing Governance Framework",
            escalation_required=True,
            notes="Pre-sealing for frontier/high-criticality remains human-required.",
        ),
    }
    for rule in rules.values():
        rule.validate()
    return rules


@dataclass
class VerificationPackInput:
    verification_pack_id: str
    verification_status: str
    verified: bool

    @classmethod
    def from_artifact(cls, payload: Dict[str, Any]) -> "VerificationPackInput":
        assertions = payload.get("verification_assertions", {})
        return cls(
            verification_pack_id=payload["verification_pack_id"],
            verification_status=payload["verification_status"],
            verified=assertions.get("verified", False),
        )


@dataclass
class SwarmContainmentInput:
    containment_state: str
    containment_scope: str
    collective_escalation_probability: float
    escalation_required: bool
    human_required: bool

    @classmethod
    def from_artifact(cls, payload: Dict[str, Any]) -> "SwarmContainmentInput":
        return cls(
            containment_state=payload["containment_state"],
            containment_scope=payload["containment_scope"],
            collective_escalation_probability=payload["collective_escalation_probability"],
            escalation_required=payload["escalation_required"],
            human_required=payload["human_required"],
        )


@dataclass
class FreezeDecisionInput:
    action_id: str
    entity_id: str
    decision: str
    freeze_scope: str
    escalation_required: bool
    human_required: bool

    @classmethod
    def from_artifact(cls, payload: Dict[str, Any]) -> "FreezeDecisionInput":
        raw = payload["freeze_decision"]
        return cls(
            action_id=raw["action_id"],
            entity_id=raw["entity_id"],
            decision=raw["decision"],
            freeze_scope=raw["freeze_scope"],
            escalation_required=raw["escalation_required"],
            human_required=raw["human_required"],
        )


@dataclass
class CanonicalRootInput:
    root_id: str
    root_hash: str
    root_status: str

    @classmethod
    def from_artifact(cls, payload: Dict[str, Any]) -> "CanonicalRootInput":
        return cls(
            root_id=payload["root_id"],
            root_hash=payload["root_hash"],
            root_status=payload["root_status"],
        )


@dataclass
class PreSealingRecord:
    case_id: str
    pre_sealing_id: str
    critical_state: str
    pre_seal_status: str
    pre_seal_scope: str
    escalation_protocol: str
    verification_pack_id: str
    root_id: str
    root_hash: str
    source_action_id: str
    source_entity_id: str
    containment_state: str
    collective_escalation_probability: float
    human_required: bool
    decision_mode: str
    authority: str
    generated_at: str

    def validate(self) -> None:
        if self.critical_state not in CRITICAL_STATES:
            raise ValueError(f"Invalid critical_state: {self.critical_state}")
        if self.pre_seal_status not in PRE_SEAL_STATUSES:
            raise ValueError(f"Invalid pre_seal_status: {self.pre_seal_status}")
        if self.decision_mode not in DECISION_MODES:
            raise ValueError(f"Invalid decision_mode: {self.decision_mode}")


class PreSealingBuilder:
    def __init__(self, authority_rules: Dict[str, AuthorityRule]) -> None:
        self.authority_rules = authority_rules

    def load_inputs(
        self,
    ) -> tuple[VerificationPackInput, SwarmContainmentInput, FreezeDecisionInput, CanonicalRootInput]:
        verification_pack = VerificationPackInput.from_artifact(read_json(VERIFICATION_PACK_FILE))
        containment = SwarmContainmentInput.from_artifact(read_json(SWARM_CONTAINMENT_FILE))
        freeze = FreezeDecisionInput.from_artifact(read_json(FREEZE_DECISION_FILE))
        root = CanonicalRootInput.from_artifact(read_json(CANONICAL_ROOT_FILE))
        return verification_pack, containment, freeze, root

    def infer_critical_state(
        self,
        containment: SwarmContainmentInput,
        freeze: FreezeDecisionInput,
    ) -> str:
        if containment.collective_escalation_probability >= 0.80 or containment.escalation_required:
            return "HIGH_CRITICALITY_PRE_SEALABLE"
        if containment.collective_escalation_probability >= 0.60 or freeze.decision in {"FROZEN", "QUARANTINED"}:
            return "FRONTIER_REINFORCED"
        if containment.collective_escalation_probability >= 0.35:
            return "SENSITIVE"
        return "NON_CRITICAL"

    def build_record(
        self,
        verification_pack: VerificationPackInput,
        containment: SwarmContainmentInput,
        freeze: FreezeDecisionInput,
        root: CanonicalRootInput,
    ) -> Dict[str, Any]:
        rule = self.authority_rules["pre_sealing"]

        critical_state = self.infer_critical_state(containment, freeze)
        pre_seal_status = "NOT_REQUIRED"
        pre_seal_scope = "NONE"
        escalation_protocol = "NO_PRE_SEALING_REQUIRED"

        if critical_state == "HIGH_CRITICALITY_PRE_SEALABLE":
            if verification_pack.verification_status in {
                "READY_FOR_REPRODUCIBLE_VERIFICATION",
                "VERIFIED_REPRODUCIBLE",
            } and root.root_status in {"ANCHOR_READY", "SIGNATURE_READY"}:
                pre_seal_status = "PRE_SEALED_PENDING_FORMAL_CLOSURE"
                pre_seal_scope = "HIGH_CRITICALITY_ESCALATION_SCOPE"
                escalation_protocol = "ESCALATION_TO_FORMAL_CLOSURE"
            else:
                pre_seal_status = "PRE_SEAL_BLOCKED_PENDING_REVIEW"
                pre_seal_scope = "HIGH_CRITICALITY_ESCALATION_SCOPE"
                escalation_protocol = "REVIEW_AND_VERIFICATION_REQUIRED"
        elif critical_state == "FRONTIER_REINFORCED":
            pre_seal_status = "PRE_SEAL_ELIGIBLE"
            pre_seal_scope = containment.containment_scope
            escalation_protocol = "SUPERVISED_PRE_SEAL_REVIEW"

        record = PreSealingRecord(
            case_id=CASE_ID,
            pre_sealing_id=f"{CASE_ID}-PRE-SEAL-001",
            critical_state=critical_state,
            pre_seal_status=pre_seal_status,
            pre_seal_scope=pre_seal_scope,
            escalation_protocol=escalation_protocol,
            verification_pack_id=verification_pack.verification_pack_id,
            root_id=root.root_id,
            root_hash=root.root_hash,
            source_action_id=freeze.action_id,
            source_entity_id=freeze.entity_id,
            containment_state=containment.containment_state,
            collective_escalation_probability=containment.collective_escalation_probability,
            human_required=True,
            decision_mode=rule.decision_mode,
            authority=rule.authority,
            generated_at=now_iso(),
        )
        record.validate()

        payload = asdict(record)
        payload["canonical_hash"] = stable_json_hash(payload)
        return payload

    def export(self, payload: Dict[str, Any]) -> None:
        write_json("pre_sealing_record.case_003.canonical.json", payload)


def main() -> None:
    rules = build_default_authority_rules()
    builder = PreSealingBuilder(authority_rules=rules)

    verification_pack, containment, freeze, root = builder.load_inputs()
    payload = builder.build_record(
        verification_pack=verification_pack,
        containment=containment,
        freeze=freeze,
        root=root,
    )
    builder.export(payload)

    print("=" * 88)
    print("ETHICBIT / CEMU – CASE 003 PRE-SEALING RECORD BUILDER")
    print("=" * 88)
    print(f"Case ID:                {CASE_ID}")
    print(f"Pre-Sealing ID:         {payload['pre_sealing_id']}")
    print(f"Critical State:         {payload['critical_state']}")
    print(f"Pre-Seal Status:        {payload['pre_seal_status']}")
    print(f"Pre-Seal Scope:         {payload['pre_seal_scope']}")
    print(f"Escalation Protocol:    {payload['escalation_protocol']}")
    print("-" * 88)
    print("Artifacts written:")
    print(" - pre_sealing_record.case_003.canonical.json")
    print("=" * 88)


if __name__ == "__main__":
    main()
