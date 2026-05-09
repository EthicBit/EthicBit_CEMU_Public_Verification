# MECH-REASON™ Engine — AEM-EVOLVE™ v1.2

**Type:** Deterministic Mechanical Reasoning Engine
**Version:** v1.2.0

---

## Constitutional rule

```
MECH-REASON™ recommends mechanically.
MechanicalGate decides deterministically.
ReceiptSealer seals.
EthicBit audits, hashes, anchors, and preserves the claim boundary.
```

## Data flow

```
Evidence Bundle + Evidence Hash + Policy Version
        ↓
Claim Boundary Checker    (R-CLAIM-* rules)
Evidence Completeness Scorer
Governance Risk Scorer
        ↓
Decision Table Evaluator  (priority: FAIL_CLOSED > ESCALATE > SCOPE > PASS)
State Machine Validator   (verifies outcome reachability)
HITL Requirement Inference
Mechanical Explanation Generator
        ↓
MECH_REASON_REPORT.json  (sealed with SHA-256 report_hash)
```

## Allowed outcomes

| Outcome | Condition |
|---|---|
| `PASS` | All checks pass, scores within thresholds |
| `SCOPE_LIMITED` | Partial evidence or moderate risk |
| `FAIL_CLOSED` | Any R-CLAIM-* rule triggered |
| `ESCALATE_TO_HITL` | High risk or sensitive domain |

## How to run

```bash
python3 demos/aem-evolve-multi-agent-api/tools/reasoning/mech_reason.py
# MECH_REASON_STATUS=PASS
# recommended_outcome: PASS | SCOPE_LIMITED | FAIL_CLOSED | ESCALATE_TO_HITL
```

## LLM boundary

LLM output is not final governance. LLM output is not official status. LLM output is not receipt sealing.

## Supported claim

> AEM-EVOLVE™ v1.2 introduces MECH-REASON™, a deterministic reasoning engine for policy-bound, evidence-based governance recommendations.
