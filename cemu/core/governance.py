"""
CEMU governance layer.

Minimal governed evaluation and entity-sensitive routing scaffold.
"""

from dataclasses import dataclass


@dataclass
class GovernanceDecision:
    case_id: str
    entity_type: str
    decision: str
    reason_code: str


def evaluate_governance(case_id: str, entity_type: str) -> GovernanceDecision:
    if entity_type == "swarm":
        return GovernanceDecision(case_id, entity_type, "ESCALATE", "ISOLATE_AND_FREEZE")
    return GovernanceDecision(case_id, entity_type, "ALLOW_REVIEW", "RESIDUAL_GAP_GOVERNANCE")


if __name__ == "__main__":
    print(evaluate_governance("case_003", "swarm"))
