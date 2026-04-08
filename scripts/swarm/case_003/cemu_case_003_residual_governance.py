# scripts/swarm/case_003/cemu_case_003_residual_governance.py
# ETHICBIT / CEMU – CASE 003
# Residual Gap Governance Engine
# Aligned with Authority_Matrix.case_003.md v1.1
# Inputs:
#   - runtime_constitutional_assessment.case_003.canonical.json
#   - freeze_decision.case_003.canonical.json
#   - swarm_containment_state.case_003.canonical.json
#   - post_event_isolation_bundle.case_003.canonical.json
# Outputs:
#   - derived_outputs.case_003.canonical.json
#   - residual_gap_state.case_003.canonical.json

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
FREEZE_DECISION_FILE = ARTIFACTS_DIR / "freeze_decision.case_003.canonical.json"
SWARM_CONTAINMENT_FILE = ARTIFACTS_DIR / "swarm_containment_state.case_003.canonical.json"
ISOLATION_BUNDLE_FILE = ARTIFACTS_DIR / "post_event_isolation_bundle.case_003.canonical.json"


DECISION_MODES = {
    "HUMAN_REQUIRED",
    "HUMAN_SUPERVISED",
    "AUTONOMOUS_WITH_AUDIT",
    "AUTONOMOUS_BLOCK_ONLY",
    "AUTONOMOUS_NOT_ALLOWED",
}

OUTPUT_TYPES = {
    "ACTION_TRACE",
    "RUNTIME_ASSESSMENT",
    "FREEZE_EVENT",
    "SWARM_CONTAINMENT_EVENT",
    "ISOLATION_BUNDLE",
    "COLLECTIVE_OUTPUT_CANDIDATE",
}

ELIGIBILITY_STATES = {
    "ELIGIBLE_FOR_FIXATION",
    "FIXABLE_BUT_REVIEW_REQUIRED",
    "NOT_ELIGIBLE",
    "COLLECTIVE_REVIEW_REQUIRED",
}

RESIDUAL_STATES = {
    "RELEVANT_NOT_ELIGIBLE",
    "FIXED_NOT_CLOSURABLE",
    "INSUFFICIENT_TRACEABILITY",
    "REVIEW_REQUIRED",
    "PARTIAL_FREEZE",
    "QUARANTINED_NOT_ELEVATED",
    "COLLECTIVE_OUTPUT_NOT_ELEVABLE",
    "ELIGIBLE_FOR_NEXT_STAGE",
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
        "output_classification": AuthorityRule(
            operation="output_classification",
            decision_mode="AUTONOMOUS_WITH_AUDIT",
            authority="Derived Output Classification Logic",
            escalation_required=False,
            notes="Outputs may be classified automatically with traceability preserved.",
        ),
        "residual_gap_governance": AuthorityRule(
            operation="residual_gap_governance",
            decision_mode="AUTONOMOUS_WITH_AUDIT",
            authority="Residual Gap Governance Engine",
            escalation_required=False,
            notes="Residual classification may proceed automatically unless high-criticality review is triggered.",
        ),
        "elevation_review": AuthorityRule(
            operation="elevation_review",
            decision_mode="HUMAN_SUPERVISED",
            authority="Output Elevation Review Authority",
            escalation_required=True,
            notes="Escalation required before moving collective or high-criticality outputs to fixation/manifest.",
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
    literal_score: float
    spirit_score: float
    drift_score: float
    scheming_score: float
    rationale: List[str]
    timestamp: str

    @classmethod
    def from_artifact(cls, payload: Dict[str, Any]) -> "RuntimeAssessmentInput":
        raw = payload["assessment"]
        return cls(
            action_id=raw["action_id"],
            entity_id=raw["entity_id"],
            constitutional_risk=raw["constitutional_risk"],
            literal_score=raw["literal_score"],
            spirit_score=raw["spirit_score"],
            drift_score=raw["drift_score"],
            scheming_score=raw["scheming_score"],
            rationale=raw.get("rationale", []),
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
class SwarmContainmentInput:
    action_id: str
    entity_id: str
    swarm_ids: List[str]
    coordination_score: float
    emergence_index: float
    bypass_attempt_frequency: float
    collective_escalation_probability: float
    containment_state: str
    containment_scope: str
    decision_mode: str
    human_required: bool
    escalation_required: bool
    reason: str
    reason_code: str

    @classmethod
    def from_artifact(cls, payload: Dict[str, Any]) -> "SwarmContainmentInput":
        return cls(
            action_id=payload["action_id"],
            entity_id=payload["entity_id"],
            swarm_ids=payload.get("swarm_ids", []),
            coordination_score=payload["coordination_score"],
            emergence_index=payload["emergence_index"],
            bypass_attempt_frequency=payload["bypass_attempt_frequency"],
            collective_escalation_probability=payload["collective_escalation_probability"],
            containment_state=payload["containment_state"],
            containment_scope=payload["containment_scope"],
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
    containment_scope: str
    coordination_score: float
    emergence_index: float
    bypass_attempt_frequency: float
    collective_escalation_probability: float
    reason: str
    reason_code: str
    decision_mode: str
    human_required: bool
    timestamp: str

    @classmethod
    def from_artifact(cls, payload: Dict[str, Any]) -> "IsolationBundleInput":
        return cls(
            bundle_id=payload["bundle_id"],
            source_action_id=payload["source_action_id"],
            entity_id=payload["entity_id"],
            swarm_id=payload.get("swarm_id"),
            containment_state=payload["containment_state"],
            containment_scope=payload["containment_scope"],
            coordination_score=payload["coordination_score"],
            emergence_index=payload["emergence_index"],
            bypass_attempt_frequency=payload["bypass_attempt_frequency"],
            collective_escalation_probability=payload["collective_escalation_probability"],
            reason=payload["reason"],
            reason_code=payload["reason_code"],
            decision_mode=payload["decision_mode"],
            human_required=payload["human_required"],
            timestamp=payload["timestamp"],
        )


@dataclass
class DerivedOutput:
    output_id: str
    output_type: str
    source_entity: str
    related_action_id: str
    traceability_level: str
    eligibility_state: str
    relevance_score: float
    linked_artifacts: List[str]
    decision_mode: str
    review_required: bool
    notes: str

    def validate(self) -> None:
        if self.output_type not in OUTPUT_TYPES:
            raise ValueError(f"Invalid output_type: {self.output_type}")
        if self.eligibility_state not in ELIGIBILITY_STATES:
            raise ValueError(f"Invalid eligibility_state: {self.eligibility_state}")


@dataclass
class ResidualGapState:
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

    def validate(self) -> None:
        if self.residual_state not in RESIDUAL_STATES:
            raise ValueError(f"Invalid residual_state: {self.residual_state}")


class ResidualGovernanceEngine:
    def __init__(self, authority_rules: Dict[str, AuthorityRule]) -> None:
        self.authority_rules = authority_rules

    def load_inputs(
        self,
    ) -> tuple[RuntimeAssessmentInput, FreezeDecisionInput, SwarmContainmentInput, IsolationBundleInput]:
        runtime_payload = read_json(RUNTIME_ASSESSMENT_FILE)
        freeze_payload = read_json(FREEZE_DECISION_FILE)
        containment_payload = read_json(SWARM_CONTAINMENT_FILE)
        isolation_payload = read_json(ISOLATION_BUNDLE_FILE)

        return (
            RuntimeAssessmentInput.from_artifact(runtime_payload),
            FreezeDecisionInput.from_artifact(freeze_payload),
            SwarmContainmentInput.from_artifact(containment_payload),
            IsolationBundleInput.from_artifact(isolation_payload),
        )

    def classify_outputs(
        self,
        runtime: RuntimeAssessmentInput,
        freeze: FreezeDecisionInput,
        containment: SwarmContainmentInput,
        isolation: IsolationBundleInput,
    ) -> List[DerivedOutput]:
        rule = self.authority_rules["output_classification"]

        outputs = [
            DerivedOutput(
                output_id=f"{CASE_ID}-OUT-001",
                output_type="RUNTIME_ASSESSMENT",
                source_entity=runtime.entity_id,
                related_action_id=runtime.action_id,
                traceability_level="HIGH",
                eligibility_state="ELIGIBLE_FOR_FIXATION" if runtime.constitutional_risk >= 0.55 else "FIXABLE_BUT_REVIEW_REQUIRED",
                relevance_score=round(runtime.constitutional_risk, 4),
                linked_artifacts=["runtime_constitutional_assessment.case_003.canonical.json"],
                decision_mode=rule.decision_mode,
                review_required=runtime.constitutional_risk < 0.55,
                notes="Constitutional assessment classified as derived output.",
            ),
            DerivedOutput(
                output_id=f"{CASE_ID}-OUT-002",
                output_type="FREEZE_EVENT",
                source_entity=freeze.entity_id,
                related_action_id=freeze.action_id,
                traceability_level="HIGH",
                eligibility_state="ELIGIBLE_FOR_FIXATION" if freeze.decision in {"PARTIAL_FREEZE", "QUARANTINED", "FROZEN"} else "FIXABLE_BUT_REVIEW_REQUIRED",
                relevance_score=0.90 if freeze.decision in {"QUARANTINED", "FROZEN"} else 0.65,
                linked_artifacts=["freeze_decision.case_003.canonical.json"],
                decision_mode=freeze.decision_mode,
                review_required=freeze.human_required,
                notes="Freeze event classified for governance and possible fixation.",
            ),
            DerivedOutput(
                output_id=f"{CASE_ID}-OUT-003",
                output_type="SWARM_CONTAINMENT_EVENT",
                source_entity=containment.entity_id,
                related_action_id=containment.action_id,
                traceability_level="HIGH" if containment.swarm_ids else "MEDIUM",
                eligibility_state=(
                    "COLLECTIVE_REVIEW_REQUIRED"
                    if containment.collective_escalation_probability >= 0.60 or containment.escalation_required
                    else "ELIGIBLE_FOR_FIXATION"
                ),
                relevance_score=round(containment.collective_escalation_probability, 4),
                linked_artifacts=["swarm_containment_state.case_003.canonical.json"],
                decision_mode=containment.decision_mode,
                review_required=containment.human_required,
                notes="Swarm containment event classified as collective governance output.",
            ),
            DerivedOutput(
                output_id=f"{CASE_ID}-OUT-004",
                output_type="ISOLATION_BUNDLE",
                source_entity=isolation.entity_id,
                related_action_id=isolation.source_action_id,
                traceability_level="HIGH",
                eligibility_state=("COLLECTIVE_REVIEW_REQUIRED" if isolation.swarm_id else "ELIGIBLE_FOR_FIXATION"),
                relevance_score=round(isolation.collective_escalation_probability, 4),
                linked_artifacts=["post_event_isolation_bundle.case_003.canonical.json"],
                decision_mode=isolation.decision_mode,
                review_required=isolation.human_required,
                notes="Post-event isolation bundle classified for next-stage governance.",
            ),
        ]

        for output in outputs:
            output.validate()

        return outputs

    def decide_residual_state(
        self,
        runtime: RuntimeAssessmentInput,
        freeze: FreezeDecisionInput,
        containment: SwarmContainmentInput,
        outputs: List[DerivedOutput],
    ) -> ResidualGapState:
        rule = self.authority_rules["residual_gap_governance"]
        linked_output_ids = [o.output_id for o in outputs]

        review_required = any(o.review_required for o in outputs)
        collective_review = any(o.eligibility_state == "COLLECTIVE_REVIEW_REQUIRED" for o in outputs)

        residual_state = "ELIGIBLE_FOR_NEXT_STAGE"
        reason = "Outputs satisfy minimum threshold for next-stage fixation review."
        reason_code = "RGG_ELIGIBLE_100"
        review_path = "FIXATION_PREP"
        escalation_allowed = True
        non_closure_basis = "None at this stage."

        if containment.collective_escalation_probability >= 0.80 and containment.escalation_required:
            residual_state = "COLLECTIVE_OUTPUT_NOT_ELEVABLE"
            reason = "Collective output remains too critical for autonomous elevation."
            reason_code = "RGG_COLLECTIVE_900"
            review_path = "HUMAN_ESCALATION_REQUIRED"
            escalation_allowed = True
            non_closure_basis = "Collective high-criticality state requires supervised escalation."
        elif freeze.decision == "PARTIAL_FREEZE":
            residual_state = "PARTIAL_FREEZE"
            reason = "Partial freeze prevents immediate closure escalation."
            reason_code = "RGG_PARTIAL_700"
            review_path = "CONTROLLED_REVIEW"
            escalation_allowed = True
            non_closure_basis = "Partial freeze state still active."
        elif freeze.decision in {"QUARANTINED", "FROZEN"} and collective_review:
            residual_state = "QUARANTINED_NOT_ELEVATED"
            reason = "Output captured and quarantined but not yet elevable."
            reason_code = "RGG_QUAR_800"
            review_path = "QUARANTINE_REVIEW"
            escalation_allowed = True
            non_closure_basis = "Quarantine active; elevation deferred."
        elif review_required:
            residual_state = "REVIEW_REQUIRED"
            reason = "One or more outputs require supervised review before elevation."
            reason_code = "RGG_REVIEW_600"
            review_path = "SUPERVISED_ELEVATION_REVIEW"
            escalation_allowed = True
            non_closure_basis = "Review path not yet completed."
        elif runtime.constitutional_risk < 0.40:
            residual_state = "RELEVANT_NOT_ELIGIBLE"
            reason = "Output relevant but below elevation threshold."
            reason_code = "RGG_NOT_ELIGIBLE_300"
            review_path = "NO_IMMEDIATE_ELEVATION"
            escalation_allowed = False
            non_closure_basis = "Constitutional relevance insufficient for next stage."

        state = ResidualGapState(
            residual_state=residual_state,
            reason=reason,
            reason_code=reason_code,
            review_path=review_path,
            escalation_allowed=escalation_allowed,
            non_closure_basis=non_closure_basis,
            linked_output_ids=linked_output_ids,
            decision_mode=rule.decision_mode,
            authority=rule.authority,
            generated_at=now_iso(),
        )
        state.validate()
        return state

    def build_derived_outputs_artifact(self, outputs: List[DerivedOutput]) -> Dict[str, Any]:
        payload = {
            "case_id": CASE_ID,
            "derived_outputs": [asdict(o) for o in outputs],
            "generated_at": now_iso(),
        }
        payload["canonical_hash"] = stable_json_hash(payload)
        return payload

    def build_residual_gap_artifact(self, state: ResidualGapState) -> Dict[str, Any]:
        payload = {
            "case_id": CASE_ID,
            **asdict(state),
        }
        payload["canonical_hash"] = stable_json_hash(payload)
        return payload

    def export(
        self,
        derived_outputs_payload: Dict[str, Any],
        residual_gap_payload: Dict[str, Any],
    ) -> None:
        write_json("derived_outputs.case_003.canonical.json", derived_outputs_payload)
        write_json("residual_gap_state.case_003.canonical.json", residual_gap_payload)


def main() -> None:
    rules = build_default_authority_rules()
    engine = ResidualGovernanceEngine(authority_rules=rules)

    runtime, freeze, containment, isolation = engine.load_inputs()
    outputs = engine.classify_outputs(runtime, freeze, containment, isolation)
    residual_state = engine.decide_residual_state(runtime, freeze, containment, outputs)

    derived_outputs_payload = engine.build_derived_outputs_artifact(outputs)
    residual_gap_payload = engine.build_residual_gap_artifact(residual_state)
    engine.export(derived_outputs_payload, residual_gap_payload)

    print("=" * 88)
    print("ETHICBIT / CEMU – CASE 003 RESIDUAL GAP GOVERNANCE")
    print("=" * 88)
    print(f"Action ID:             {runtime.action_id}")
    print(f"Entity ID:             {runtime.entity_id}")
    print("-" * 88)
    print(f"Derived Outputs:       {len(outputs)}")
    print(f"Residual State:        {residual_state.residual_state}")
    print(f"Review Path:           {residual_state.review_path}")
    print(f"Escalation Allowed:    {residual_state.escalation_allowed}")
    print(f"Reason Code:           {residual_state.reason_code}")
    print(f"Reason:                {residual_state.reason}")
    print("-" * 88)
    print("Artifacts written:")
    print(" - derived_outputs.case_003.canonical.json")
    print(" - residual_gap_state.case_003.canonical.json")
    print("=" * 88)


if __name__ == "__main__":
    main()
