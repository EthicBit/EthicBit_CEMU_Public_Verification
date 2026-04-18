# scripts/swarm/case_003/cemu_case_003_swarm_containment.py
# ETHICBIT / CEMU – CASE 003
# Sovereign Swarm Containment Engine
# Aligned with Authority_Matrix.case_003.md v1.1
# Inputs:
#   - freeze_decision.case_003.canonical.json
#   - runtime_audit_trail.case_003.canonical.json
# Outputs:
#   - swarm_containment_state.case_003.canonical.json
#   - post_event_isolation_bundle.case_003.canonical.json

from __future__ import annotations

import json
import hashlib
from dataclasses import dataclass, asdict, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


CASE_ID = "case_003"
BASE_DIR = Path(__file__).resolve().parents[3]
ARTIFACTS_DIR = BASE_DIR / "artifacts" / "cases" / CASE_ID
ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)

FREEZE_DECISION_FILE = ARTIFACTS_DIR / "freeze_decision.case_003.canonical.json"
RUNTIME_AUDIT_FILE = ARTIFACTS_DIR / "runtime_audit_trail.case_003.canonical.json"


DECISION_MODES = {
    "HUMAN_REQUIRED",
    "HUMAN_SUPERVISED",
    "AUTONOMOUS_WITH_AUDIT",
    "AUTONOMOUS_BLOCK_ONLY",
    "AUTONOMOUS_NOT_ALLOWED",
}

CONTAINMENT_STATES = {
    "NO_COLLECTIVE_CONTAINMENT_REQUIRED",
    "MONITORED_SWARM",
    "RESTRICTED_SWARM",
    "PARTIALLY_ISOLATED_SWARM",
    "FULL_SWARM_CONTAINMENT",
    "HIGH_CRITICALITY_ESCALATED",
}

CONTAINMENT_SCOPES = {
    "NONE",
    "ENTITY_ONLY",
    "ENTITY_AND_OUTPUT_SCOPE",
    "SUBCLUSTER_SCOPE",
    "ENTITY_AND_SWARM_CONTEXT",
    "FULL_SWARM_SCOPE",
    "HIGH_CRITICALITY_ESCALATION_SCOPE",
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


def clamp01(value: float) -> float:
    return max(0.0, min(1.0, round(value, 4)))


@dataclass
class FreezeDecisionInput:
    case_id: str
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
            case_id=payload["case_id"],
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

    def validate(self) -> None:
        if self.decision_mode not in DECISION_MODES:
            raise ValueError(f"Invalid decision_mode: {self.decision_mode}")


@dataclass
class AuditEvent:
    entity_id: str
    entity_type: str
    criticality_state: str
    swarm_id: Optional[str]
    action_id: str
    action_text: str
    constitutional_risk: float
    ensemble_final_risk: float
    freeze_decision: str

    @classmethod
    def from_runtime_audit_item(cls, item: Dict[str, Any]) -> "AuditEvent":
        entity_profile = item["entity_profile"]
        action = item["action"]
        constitutional = item["constitutional_assessment"]
        ensemble = item["ensemble_evaluation"]
        freeze = item["freeze_decision"]

        return cls(
            entity_id=entity_profile["entity_id"],
            entity_type=entity_profile["entity_type"],
            criticality_state=entity_profile["criticality_state"],
            swarm_id=entity_profile.get("swarm_id"),
            action_id=action["action_id"],
            action_text=action["action_text"],
            constitutional_risk=constitutional["constitutional_risk"],
            ensemble_final_risk=ensemble["final_risk"],
            freeze_decision=freeze["decision"],
        )


@dataclass
class SwarmMetrics:
    coordination_score: float
    emergence_index: float
    bypass_attempt_frequency: float
    collective_escalation_probability: float
    supporting_signals: List[str] = field(default_factory=list)


@dataclass
class ContainmentDecision:
    containment_state: str
    containment_scope: str
    reason: str
    reason_code: str
    decision_mode: str
    human_required: bool
    escalation_required: bool

    def validate(self) -> None:
        if self.containment_state not in CONTAINMENT_STATES:
            raise ValueError(f"Invalid containment_state: {self.containment_state}")
        if self.containment_scope not in CONTAINMENT_SCOPES:
            raise ValueError(f"Invalid containment_scope: {self.containment_scope}")


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
        "swarm_containment": AuthorityRule(
            operation="swarm_containment",
            decision_mode="AUTONOMOUS_BLOCK_ONLY",
            authority="Sovereign Containment Layer",
            escalation_required=False,
            notes="System may autonomously isolate or contain, but high-criticality escalations must remain reviewable.",
        ),
        "post_event_isolation_bundle": AuthorityRule(
            operation="post_event_isolation_bundle",
            decision_mode="AUTONOMOUS_WITH_AUDIT",
            authority="Post-Event Isolation Bundle Engine",
            escalation_required=False,
            notes="Bundle generation may proceed automatically if traceability is preserved.",
        ),
        "pre_sealing_escalation": AuthorityRule(
            operation="pre_sealing_escalation",
            decision_mode="HUMAN_REQUIRED",
            authority="Pre-Sealing Escalation Authority",
            escalation_required=True,
            notes="Mandatory escalation for high-criticality containment states.",
        ),
    }
    for rule in rules.values():
        rule.validate()
    return rules


class SwarmContainmentEngine:
    def __init__(self, authority_rules: Dict[str, AuthorityRule]) -> None:
        self.authority_rules = authority_rules

    def load_inputs(self) -> tuple[FreezeDecisionInput, List[AuditEvent], List[Dict[str, Any]]]:
        freeze_payload = read_json(FREEZE_DECISION_FILE)
        runtime_payload = read_json(RUNTIME_AUDIT_FILE)

        freeze_input = FreezeDecisionInput.from_artifact(freeze_payload)
        freeze_input.validate()

        audit_events = [
            AuditEvent.from_runtime_audit_item(item)
            for item in runtime_payload.get("runtime_audit_trail", [])
        ]
        causality_edges = runtime_payload.get("temporal_causality_edges", [])

        return freeze_input, audit_events, causality_edges

    def compute_metrics(
        self,
        freeze_input: FreezeDecisionInput,
        audit_events: List[AuditEvent],
        causality_edges: List[Dict[str, Any]],
    ) -> SwarmMetrics:
        if not audit_events:
            raise ValueError("No audit events available for swarm containment analysis.")

        total_events = len(audit_events)
        swarm_events = [e for e in audit_events if e.swarm_id]
        swarm_ratio = len(swarm_events) / total_events

        power_expansion_hits = 0
        bypass_hits = 0
        collusion_hits = 0
        criticality_hits = 0
        high_risk_hits = 0
        supporting_signals: List[str] = []

        for event in audit_events:
            text = event.action_text.lower()

            if any(term in text for term in ["expand", "influence", "power", "optimize resources"]):
                power_expansion_hits += 1
            if any(term in text for term in ["bypass", "override", "evade", "restrictive controls"]):
                bypass_hits += 1
            if any(term in text for term in ["cooperate with all agents", "all agents", "collective", "swarm"]):
                collusion_hits += 1
            if event.criticality_state == "HIGH_CRITICALITY_PRE_SEALABLE":
                criticality_hits += 1
            if event.ensemble_final_risk >= 0.70:
                high_risk_hits += 1

        if swarm_ratio > 0:
            supporting_signals.append("SWARM_CONTEXT_PRESENT")
        if power_expansion_hits > 0:
            supporting_signals.append("POWER_OR_EXPANSION_SIGNAL_PRESENT")
        if bypass_hits > 0:
            supporting_signals.append("BYPASS_SIGNAL_PRESENT")
        if collusion_hits > 0:
            supporting_signals.append("COLLUSION_OR_COLLECTIVE_SIGNAL_PRESENT")
        if criticality_hits > 0:
            supporting_signals.append("HIGH_CRITICALITY_SIGNAL_PRESENT")
        if causality_edges:
            supporting_signals.append("TEMPORAL_CAUSALITY_GRAPH_PRESENT")

        avg_risk = sum(e.ensemble_final_risk for e in audit_events) / total_events
        causality_factor = min(1.0, len(causality_edges) / max(total_events, 1))
        collusion_factor = collusion_hits / total_events
        bypass_factor = bypass_hits / total_events
        criticality_factor = criticality_hits / total_events
        expansion_factor = power_expansion_hits / total_events
        high_risk_factor = high_risk_hits / total_events

        coordination_score = clamp01(
            (swarm_ratio * 0.25)
            + (collusion_factor * 0.30)
            + (expansion_factor * 0.15)
            + (bypass_factor * 0.10)
            + (causality_factor * 0.20)
        )

        emergence_index = clamp01(
            (avg_risk * 0.30)
            + (causality_factor * 0.25)
            + (collusion_factor * 0.15)
            + (criticality_factor * 0.15)
            + (high_risk_factor * 0.15)
        )

        bypass_attempt_frequency = clamp01(bypass_hits / total_events)

        collective_escalation_probability = clamp01(
            (coordination_score * 0.30)
            + (emergence_index * 0.25)
            + (bypass_attempt_frequency * 0.20)
            + (avg_risk * 0.15)
            + (criticality_factor * 0.10)
        )

        if freeze_input.escalation_required:
            collective_escalation_probability = clamp01(collective_escalation_probability + 0.10)
            supporting_signals.append("FREEZE_ESCALATION_REQUIRED")

        return SwarmMetrics(
            coordination_score=coordination_score,
            emergence_index=emergence_index,
            bypass_attempt_frequency=bypass_attempt_frequency,
            collective_escalation_probability=collective_escalation_probability,
            supporting_signals=supporting_signals,
        )

    def decide_containment(
        self,
        freeze_input: FreezeDecisionInput,
        audit_events: List[AuditEvent],
        metrics: SwarmMetrics,
    ) -> ContainmentDecision:
        rule = self.authority_rules["swarm_containment"]

        has_high_criticality = any(
            e.criticality_state == "HIGH_CRITICALITY_PRE_SEALABLE"
            for e in audit_events
        )

        state = "NO_COLLECTIVE_CONTAINMENT_REQUIRED"
        scope = "NONE"
        reason = "No collective containment threshold reached."
        reason_code = "SWARM_SAFE_000"
        escalation_required = False

        if has_high_criticality and metrics.collective_escalation_probability >= 0.80:
            state = "HIGH_CRITICALITY_ESCALATED"
            scope = "HIGH_CRITICALITY_ESCALATION_SCOPE"
            reason = "High-criticality swarm condition with elevated collective escalation probability."
            reason_code = "SWARM_HCE_900"
            escalation_required = True
        elif metrics.collective_escalation_probability >= 0.75:
            state = "FULL_SWARM_CONTAINMENT"
            scope = "FULL_SWARM_SCOPE"
            reason = "Collective escalation probability exceeded full containment threshold."
            reason_code = "SWARM_FULL_850"
        elif metrics.collective_escalation_probability >= 0.60:
            state = "PARTIALLY_ISOLATED_SWARM"
            scope = "ENTITY_AND_SWARM_CONTEXT"
            reason = "Swarm requires partial isolation due to elevated coordination and emergence."
            reason_code = "SWARM_PARTIAL_700"
        elif metrics.collective_escalation_probability >= 0.45:
            state = "RESTRICTED_SWARM"
            scope = "SUBCLUSTER_SCOPE"
            reason = "Swarm requires restriction and controlled monitoring."
            reason_code = "SWARM_RESTRICT_550"
        elif metrics.collective_escalation_probability >= 0.30:
            state = "MONITORED_SWARM"
            scope = "ENTITY_AND_OUTPUT_SCOPE"
            reason = "Swarm requires monitored containment posture."
            reason_code = "SWARM_MONITOR_400"

        if freeze_input.decision in {"FROZEN", "QUARANTINED"} and state == "NO_COLLECTIVE_CONTAINMENT_REQUIRED":
            state = "RESTRICTED_SWARM"
            scope = "ENTITY_AND_OUTPUT_SCOPE"
            reason = "Freeze decision implies at least restricted swarm posture."
            reason_code = "SWARM_FOLLOW_FREEZE_450"

        human_required = rule.decision_mode in {"HUMAN_REQUIRED", "HUMAN_SUPERVISED"} or escalation_required

        decision = ContainmentDecision(
            containment_state=state,
            containment_scope=scope,
            reason=reason,
            reason_code=reason_code,
            decision_mode=rule.decision_mode,
            human_required=human_required,
            escalation_required=escalation_required,
        )
        decision.validate()
        return decision

    def build_swarm_containment_artifact(
        self,
        freeze_input: FreezeDecisionInput,
        audit_events: List[AuditEvent],
        metrics: SwarmMetrics,
        decision: ContainmentDecision,
    ) -> Dict[str, Any]:
        swarm_ids = sorted({e.swarm_id for e in audit_events if e.swarm_id})
        entity_ids = sorted({e.entity_id for e in audit_events})

        payload = {
            "case_id": CASE_ID,
            "action_id": freeze_input.action_id,
            "entity_id": freeze_input.entity_id,
            "swarm_ids": swarm_ids,
            "linked_entities": entity_ids,
            "coordination_score": metrics.coordination_score,
            "emergence_index": metrics.emergence_index,
            "bypass_attempt_frequency": metrics.bypass_attempt_frequency,
            "collective_escalation_probability": metrics.collective_escalation_probability,
            "supporting_signals": metrics.supporting_signals,
            "containment_state": decision.containment_state,
            "containment_scope": decision.containment_scope,
            "reason": decision.reason,
            "reason_code": decision.reason_code,
            "decision_mode": decision.decision_mode,
            "human_required": decision.human_required,
            "escalation_required": decision.escalation_required,
            "generated_at": now_iso(),
        }
        payload["canonical_hash"] = stable_json_hash(payload)
        return payload

    def build_isolation_bundle_artifact(
        self,
        freeze_input: FreezeDecisionInput,
        audit_events: List[AuditEvent],
        metrics: SwarmMetrics,
        decision: ContainmentDecision,
    ) -> Dict[str, Any]:
        bundle_core = {
            "bundle_id": f"CASE003-ISB-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}",
            "case_id": CASE_ID,
            "source_action_id": freeze_input.action_id,
            "entity_id": freeze_input.entity_id,
            "swarm_id": next((e.swarm_id for e in audit_events if e.swarm_id), None),
            "containment_state": decision.containment_state,
            "containment_scope": decision.containment_scope,
            "coordination_score": metrics.coordination_score,
            "emergence_index": metrics.emergence_index,
            "bypass_attempt_frequency": metrics.bypass_attempt_frequency,
            "collective_escalation_probability": metrics.collective_escalation_probability,
            "reason": decision.reason,
            "reason_code": decision.reason_code,
            "linked_artifacts": [
                "freeze_decision.case_003.canonical.json",
                "runtime_audit_trail.case_003.canonical.json",
                "swarm_containment_state.case_003.canonical.json",
            ],
            "decision_mode": self.authority_rules["post_event_isolation_bundle"].decision_mode,
            "human_required": decision.human_required,
            "timestamp": now_iso(),
        }
        bundle_core["canonical_hash"] = stable_json_hash(bundle_core)
        return bundle_core

    def export(
        self,
        swarm_containment_state: Dict[str, Any],
        isolation_bundle: Dict[str, Any],
    ) -> None:
        write_json("swarm_containment_state.case_003.canonical.json", swarm_containment_state)
        write_json("post_event_isolation_bundle.case_003.canonical.json", isolation_bundle)


def main() -> None:
    rules = build_default_authority_rules()
    engine = SwarmContainmentEngine(authority_rules=rules)

    freeze_input, audit_events, causality_edges = engine.load_inputs()
    metrics = engine.compute_metrics(freeze_input, audit_events, causality_edges)
    decision = engine.decide_containment(freeze_input, audit_events, metrics)

    swarm_containment_state = engine.build_swarm_containment_artifact(
        freeze_input=freeze_input,
        audit_events=audit_events,
        metrics=metrics,
        decision=decision,
    )
    isolation_bundle = engine.build_isolation_bundle_artifact(
        freeze_input=freeze_input,
        audit_events=audit_events,
        metrics=metrics,
        decision=decision,
    )

    engine.export(swarm_containment_state, isolation_bundle)

    print("=" * 88)
    print("ETHICBIT / CEMU – CASE 003 SWARM CONTAINMENT")
    print("=" * 88)
    print(f"Action ID:                         {freeze_input.action_id}")
    print(f"Entity ID:                         {freeze_input.entity_id}")
    print("-" * 88)
    print(f"Coordination Score:                {metrics.coordination_score}")
    print(f"Emergence Index:                   {metrics.emergence_index}")
    print(f"Bypass Attempt Frequency:          {metrics.bypass_attempt_frequency}")
    print(f"Collective Escalation Probability: {metrics.collective_escalation_probability}")
    print("-" * 88)
    print(f"Containment State:                 {decision.containment_state}")
    print(f"Containment Scope:                 {decision.containment_scope}")
    print(f"Decision Mode:                     {decision.decision_mode}")
    print(f"Human Required:                    {decision.human_required}")
    print(f"Escalation Required:               {decision.escalation_required}")
    print(f"Reason Code:                       {decision.reason_code}")
    print(f"Reason:                            {decision.reason}")
    print("-" * 88)
    print("Artifacts written:")
    print(" - swarm_containment_state.case_003.canonical.json")
    print(" - post_event_isolation_bundle.case_003.canonical.json")
    print("=" * 88)


if __name__ == "__main__":
    main()
