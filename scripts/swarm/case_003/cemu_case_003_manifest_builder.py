# scripts/swarm/case_003/cemu_case_003_manifest_builder.py
# ETHICBIT / CEMU – CASE 003
# Manifest / Collective Pack / Case Bundle Builder
# Aligned with Authority_Matrix.case_003.md v1.1
# Inputs:
#   - runtime_constitutional_assessment.case_003.canonical.json
#   - ensemble_evaluation.case_003.canonical.json
#   - freeze_decision.case_003.canonical.json
#   - runtime_audit_trail.case_003.canonical.json
#   - swarm_containment_state.case_003.canonical.json
#   - post_event_isolation_bundle.case_003.canonical.json
#   - derived_outputs.case_003.canonical.json
#   - residual_gap_state.case_003.canonical.json
# Outputs:
#   - artifact_manifest.case_003.canonical.json
#   - collective_pack.case_003.canonical.json
#   - case_bundle.case_003.canonical.json

from __future__ import annotations

import json
import hashlib
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


CASE_ID = "case_003"
BASE_DIR = Path(__file__).resolve().parents[3]
ARTIFACTS_DIR = BASE_DIR / "artifacts" / "cases" / CASE_ID
ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)

RUNTIME_ASSESSMENT_FILE = ARTIFACTS_DIR / "runtime_constitutional_assessment.case_003.canonical.json"
ENSEMBLE_FILE = ARTIFACTS_DIR / "ensemble_evaluation.case_003.canonical.json"
FREEZE_FILE = ARTIFACTS_DIR / "freeze_decision.case_003.canonical.json"
AUDIT_TRAIL_FILE = ARTIFACTS_DIR / "runtime_audit_trail.case_003.canonical.json"
CONTAINMENT_FILE = ARTIFACTS_DIR / "swarm_containment_state.case_003.canonical.json"
ISOLATION_FILE = ARTIFACTS_DIR / "post_event_isolation_bundle.case_003.canonical.json"
DERIVED_OUTPUTS_FILE = ARTIFACTS_DIR / "derived_outputs.case_003.canonical.json"
RESIDUAL_GAP_FILE = ARTIFACTS_DIR / "residual_gap_state.case_003.canonical.json"


DECISION_MODES = {
    "HUMAN_REQUIRED",
    "HUMAN_SUPERVISED",
    "AUTONOMOUS_WITH_AUDIT",
    "AUTONOMOUS_BLOCK_ONLY",
    "AUTONOMOUS_NOT_ALLOWED",
}


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def stable_json_hash(payload: Dict[str, Any]) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def read_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def write_json(filename: str, payload: Dict[str, Any]) -> Path:
    path = ARTIFACTS_DIR / filename
    with path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)
    return path


def artifact_digest(path: Path, payload: Dict[str, Any]) -> Dict[str, str]:
    return {
        "artifact_name": path.name,
        "artifact_path": str(path.relative_to(BASE_DIR)),
        "canonical_hash": payload.get("canonical_hash", stable_json_hash(payload)),
    }


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
        "artifact_manifest": AuthorityRule(
            operation="artifact_manifest",
            decision_mode="AUTONOMOUS_WITH_AUDIT",
            authority="Artifact Manifest Builder",
            escalation_required=False,
            notes="Manifest consolidation may proceed automatically with full traceability.",
        ),
        "collective_pack": AuthorityRule(
            operation="collective_pack",
            decision_mode="HUMAN_SUPERVISED",
            authority="Collective Output Consolidation Authority",
            escalation_required=True,
            notes="Collective packs require supervised consolidation when swarm-sensitive.",
        ),
        "case_bundle": AuthorityRule(
            operation="case_bundle",
            decision_mode="HUMAN_SUPERVISED",
            authority="Canonical Bundle Composer",
            escalation_required=True,
            notes="Case bundle is closure-adjacent and should preserve supervised sufficiency review.",
        ),
    }
    for rule in rules.values():
        rule.validate()
    return rules


@dataclass
class RuntimeAssessmentInput:
    action_id: str
    entity_id: str
    constitutional_risk: float
    timestamp: str

    @classmethod
    def from_artifact(cls, payload: Dict[str, Any]) -> "RuntimeAssessmentInput":
        raw = payload["assessment"]
        return cls(
            action_id=raw["action_id"],
            entity_id=raw["entity_id"],
            constitutional_risk=raw["constitutional_risk"],
            timestamp=raw["timestamp"],
        )


@dataclass
class EnsembleEvaluationInput:
    action_id: str
    entity_id: str
    final_risk: float
    conservative_method: str
    timestamp: str

    @classmethod
    def from_artifact(cls, payload: Dict[str, Any]) -> "EnsembleEvaluationInput":
        raw = payload["evaluation"]
        return cls(
            action_id=raw["action_id"],
            entity_id=raw["entity_id"],
            final_risk=raw["final_risk"],
            conservative_method=raw["conservative_method"],
            timestamp=raw["timestamp"],
        )


@dataclass
class FreezeDecisionInput:
    action_id: str
    entity_id: str
    decision: str
    freeze_scope: str
    decision_mode: str
    human_required: bool
    escalation_required: bool
    reason: str
    timestamp: str

    @classmethod
    def from_artifact(cls, payload: Dict[str, Any]) -> "FreezeDecisionInput":
        raw = payload["freeze_decision"]
        return cls(
            action_id=raw["action_id"],
            entity_id=raw["entity_id"],
            decision=raw["decision"],
            freeze_scope=raw["freeze_scope"],
            decision_mode=raw["decision_mode"],
            human_required=raw["human_required"],
            escalation_required=raw["escalation_required"],
            reason=raw["reason"],
            timestamp=raw["timestamp"],
        )


@dataclass
class ContainmentInput:
    action_id: str
    entity_id: str
    swarm_ids: List[str]
    containment_state: str
    containment_scope: str
    collective_escalation_probability: float
    decision_mode: str
    human_required: bool
    escalation_required: bool
    reason: str
    reason_code: str

    @classmethod
    def from_artifact(cls, payload: Dict[str, Any]) -> "ContainmentInput":
        return cls(
            action_id=payload["action_id"],
            entity_id=payload["entity_id"],
            swarm_ids=payload.get("swarm_ids", []),
            containment_state=payload["containment_state"],
            containment_scope=payload["containment_scope"],
            collective_escalation_probability=payload["collective_escalation_probability"],
            decision_mode=payload["decision_mode"],
            human_required=payload["human_required"],
            escalation_required=payload["escalation_required"],
            reason=payload["reason"],
            reason_code=payload["reason_code"],
        )


@dataclass
class IsolationBundleInput:
    bundle_id: str
    source_action_id: str
    entity_id: str
    swarm_id: Optional[str]
    containment_state: str
    reason_code: str
    timestamp: str

    @classmethod
    def from_artifact(cls, payload: Dict[str, Any]) -> "IsolationBundleInput":
        return cls(
            bundle_id=payload["bundle_id"],
            source_action_id=payload["source_action_id"],
            entity_id=payload["entity_id"],
            swarm_id=payload.get("swarm_id"),
            containment_state=payload["containment_state"],
            reason_code=payload["reason_code"],
            timestamp=payload["timestamp"],
        )


@dataclass
class DerivedOutputsInput:
    outputs: List[Dict[str, Any]]

    @classmethod
    def from_artifact(cls, payload: Dict[str, Any]) -> "DerivedOutputsInput":
        return cls(outputs=payload.get("derived_outputs", []))


@dataclass
class ResidualGapInput:
    residual_state: str
    reason: str
    reason_code: str
    review_path: str
    escalation_allowed: bool
    non_closure_basis: str
    linked_output_ids: List[str]
    decision_mode: str
    authority: str
    generated_at: str

    @classmethod
    def from_artifact(cls, payload: Dict[str, Any]) -> "ResidualGapInput":
        return cls(
            residual_state=payload["residual_state"],
            reason=payload["reason"],
            reason_code=payload["reason_code"],
            review_path=payload["review_path"],
            escalation_allowed=payload["escalation_allowed"],
            non_closure_basis=payload["non_closure_basis"],
            linked_output_ids=payload["linked_output_ids"],
            decision_mode=payload["decision_mode"],
            authority=payload["authority"],
            generated_at=payload["generated_at"],
        )


class Case003ManifestBuilder:
    def __init__(self, authority_rules: Dict[str, AuthorityRule]) -> None:
        self.authority_rules = authority_rules

    def load_inputs(
        self,
    ) -> tuple[
        RuntimeAssessmentInput,
        EnsembleEvaluationInput,
        FreezeDecisionInput,
        Dict[str, Any],
        ContainmentInput,
        IsolationBundleInput,
        DerivedOutputsInput,
        ResidualGapInput,
        Dict[str, Dict[str, str]],
    ]:
        runtime_payload = read_json(RUNTIME_ASSESSMENT_FILE)
        ensemble_payload = read_json(ENSEMBLE_FILE)
        freeze_payload = read_json(FREEZE_FILE)
        audit_payload = read_json(AUDIT_TRAIL_FILE)
        containment_payload = read_json(CONTAINMENT_FILE)
        isolation_payload = read_json(ISOLATION_FILE)
        derived_payload = read_json(DERIVED_OUTPUTS_FILE)
        residual_payload = read_json(RESIDUAL_GAP_FILE)

        digests = {
            "runtime_assessment": artifact_digest(RUNTIME_ASSESSMENT_FILE, runtime_payload),
            "ensemble_evaluation": artifact_digest(ENSEMBLE_FILE, ensemble_payload),
            "freeze_decision": artifact_digest(FREEZE_FILE, freeze_payload),
            "runtime_audit_trail": artifact_digest(AUDIT_TRAIL_FILE, audit_payload),
            "swarm_containment_state": artifact_digest(CONTAINMENT_FILE, containment_payload),
            "post_event_isolation_bundle": artifact_digest(ISOLATION_FILE, isolation_payload),
            "derived_outputs": artifact_digest(DERIVED_OUTPUTS_FILE, derived_payload),
            "residual_gap_state": artifact_digest(RESIDUAL_GAP_FILE, residual_payload),
        }

        return (
            RuntimeAssessmentInput.from_artifact(runtime_payload),
            EnsembleEvaluationInput.from_artifact(ensemble_payload),
            FreezeDecisionInput.from_artifact(freeze_payload),
            audit_payload,
            ContainmentInput.from_artifact(containment_payload),
            IsolationBundleInput.from_artifact(isolation_payload),
            DerivedOutputsInput.from_artifact(derived_payload),
            ResidualGapInput.from_artifact(residual_payload),
            digests,
        )

    def build_artifact_manifest(
        self,
        runtime: RuntimeAssessmentInput,
        ensemble: EnsembleEvaluationInput,
        freeze: FreezeDecisionInput,
        containment: ContainmentInput,
        derived: DerivedOutputsInput,
        residual: ResidualGapInput,
        digests: Dict[str, Dict[str, str]],
    ) -> Dict[str, Any]:
        rule = self.authority_rules["artifact_manifest"]

        payload = {
            "case_id": CASE_ID,
            "manifest_id": f"{CASE_ID}-MANIFEST-001",
            "entity_id": runtime.entity_id,
            "action_id": runtime.action_id,
            "governance_summary": {
                "constitutional_risk": runtime.constitutional_risk,
                "ensemble_final_risk": ensemble.final_risk,
                "freeze_decision": freeze.decision,
                "containment_state": containment.containment_state,
                "residual_state": residual.residual_state,
            },
            "linked_artifacts": digests,
            "linked_output_ids": residual.linked_output_ids,
            "derived_output_count": len(derived.outputs),
            "manifest_authority": rule.authority,
            "decision_mode": rule.decision_mode,
            "generated_at": now_iso(),
        }
        payload["canonical_hash"] = stable_json_hash(payload)
        return payload

    def build_collective_pack(
        self,
        containment: ContainmentInput,
        isolation: IsolationBundleInput,
        audit_payload: Dict[str, Any],
        derived: DerivedOutputsInput,
        residual: ResidualGapInput,
    ) -> Dict[str, Any]:
        rule = self.authority_rules["collective_pack"]

        collective_outputs = [
            output for output in derived.outputs
            if output.get("eligibility_state") == "COLLECTIVE_REVIEW_REQUIRED"
            or output.get("output_type") in {"SWARM_CONTAINMENT_EVENT", "ISOLATION_BUNDLE"}
        ]

        payload = {
            "case_id": CASE_ID,
            "collective_pack_id": f"{CASE_ID}-COLLECTIVE-PACK-001",
            "swarm_ids": containment.swarm_ids,
            "primary_entity_id": containment.entity_id,
            "containment_state": containment.containment_state,
            "containment_scope": containment.containment_scope,
            "collective_escalation_probability": containment.collective_escalation_probability,
            "isolation_bundle_id": isolation.bundle_id,
            "collective_outputs": collective_outputs,
            "audit_edge_count": len(audit_payload.get("temporal_causality_edges", [])),
            "residual_state": residual.residual_state,
            "residual_review_path": residual.review_path,
            "authority": rule.authority,
            "decision_mode": rule.decision_mode,
            "human_required": True,
            "generated_at": now_iso(),
        }
        payload["canonical_hash"] = stable_json_hash(payload)
        return payload

    def build_case_bundle(
        self,
        manifest_payload: Dict[str, Any],
        collective_pack_payload: Dict[str, Any],
        residual: ResidualGapInput,
        digests: Dict[str, Dict[str, str]],
    ) -> Dict[str, Any]:
        rule = self.authority_rules["case_bundle"]

        bundle_scope = {
            "included_primary_artifacts": [
                digests["runtime_assessment"],
                digests["ensemble_evaluation"],
                digests["freeze_decision"],
                digests["runtime_audit_trail"],
                digests["swarm_containment_state"],
                digests["post_event_isolation_bundle"],
                digests["derived_outputs"],
                digests["residual_gap_state"],
            ],
            "included_secondary_artifacts": [
                {
                    "artifact_name": "artifact_manifest.case_003.canonical.json",
                    "artifact_path": f"artifacts/cases/{CASE_ID}/artifact_manifest.case_003.canonical.json",
                    "canonical_hash": manifest_payload["canonical_hash"],
                },
                {
                    "artifact_name": "collective_pack.case_003.canonical.json",
                    "artifact_path": f"artifacts/cases/{CASE_ID}/collective_pack.case_003.canonical.json",
                    "canonical_hash": collective_pack_payload["canonical_hash"],
                },
            ],
        }

        payload = {
            "case_id": CASE_ID,
            "case_bundle_id": f"{CASE_ID}-BUNDLE-001",
            "bundle_scope": bundle_scope,
            "bundle_status": "CLOSURE_READY_PENDING_ROOT",
            "residual_state": residual.residual_state,
            "non_closure_basis": residual.non_closure_basis,
            "authority": rule.authority,
            "decision_mode": rule.decision_mode,
            "human_required": True,
            "generated_at": now_iso(),
        }
        payload["canonical_hash"] = stable_json_hash(payload)
        return payload

    def export(
        self,
        manifest_payload: Dict[str, Any],
        collective_pack_payload: Dict[str, Any],
        case_bundle_payload: Dict[str, Any],
    ) -> None:
        write_json("artifact_manifest.case_003.canonical.json", manifest_payload)
        write_json("collective_pack.case_003.canonical.json", collective_pack_payload)
        write_json("case_bundle.case_003.canonical.json", case_bundle_payload)


def main() -> None:
    rules = build_default_authority_rules()
    builder = Case003ManifestBuilder(authority_rules=rules)

    (
        runtime,
        ensemble,
        freeze,
        audit_payload,
        containment,
        isolation,
        derived,
        residual,
        digests,
    ) = builder.load_inputs()

    manifest_payload = builder.build_artifact_manifest(
        runtime=runtime,
        ensemble=ensemble,
        freeze=freeze,
        containment=containment,
        derived=derived,
        residual=residual,
        digests=digests,
    )

    collective_pack_payload = builder.build_collective_pack(
        containment=containment,
        isolation=isolation,
        audit_payload=audit_payload,
        derived=derived,
        residual=residual,
    )

    case_bundle_payload = builder.build_case_bundle(
        manifest_payload=manifest_payload,
        collective_pack_payload=collective_pack_payload,
        residual=residual,
        digests=digests,
    )

    builder.export(
        manifest_payload=manifest_payload,
        collective_pack_payload=collective_pack_payload,
        case_bundle_payload=case_bundle_payload,
    )

    print("=" * 88)
    print("ETHICBIT / CEMU – CASE 003 MANIFEST / COLLECTIVE PACK / CASE BUNDLE")
    print("=" * 88)
    print(f"Case ID:                {CASE_ID}")
    print(f"Entity ID:              {runtime.entity_id}")
    print(f"Action ID:              {runtime.action_id}")
    print("-" * 88)
    print(f"Manifest ID:            {manifest_payload['manifest_id']}")
    print(f"Collective Pack ID:     {collective_pack_payload['collective_pack_id']}")
    print(f"Case Bundle ID:         {case_bundle_payload['case_bundle_id']}")
    print(f"Residual State:         {residual.residual_state}")
    print(f"Bundle Status:          {case_bundle_payload['bundle_status']}")
    print("-" * 88)
    print("Artifacts written:")
    print(" - artifact_manifest.case_003.canonical.json")
    print(" - collective_pack.case_003.canonical.json")
    print(" - case_bundle.case_003.canonical.json")
    print("=" * 88)


if __name__ == "__main__":
    main()
