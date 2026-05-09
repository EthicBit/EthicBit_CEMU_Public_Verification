# Optional LLM Advisory Adapter — Boundary Definition
# AEM-EVOLVE™ v1.2

**Status:** Boundary defined. Adapter is optional and non-governing.
**Version:** 1.2.0
**Scope:** Defines the precise role any LLM may play relative to MECH-REASON™.

---

## Constitutional boundary statement

```
EthicBit does not outsource governance reasoning to an LLM.

MECH-REASON™ is the governance layer.
An LLM may advise. It does not decide.
An LLM may narrate. It does not seal.
An LLM may surface context. It does not anchor.
```

---

## What the adapter IS

The Optional LLM Advisory Adapter is a **read-only, post-hoc interface** that:

| Permitted function | Description |
|---|---|
| **Narrative summarization** | Rephrases MECH_REASON_REPORT.json into prose for human-readable dashboards |
| **Risk context surfacing** | Highlights triggered rules or score anomalies in natural language |
| **Audit trail annotation** | Adds natural-language notes to sealed assurance artifacts |
| **HITL briefing generation** | Generates a human-readable brief when `ESCALATE_TO_HITL` is recommended |

---

## What the adapter IS NOT

| Prohibited function | Why prohibited |
|---|---|
| **Evaluating evidence bundles** | Evidence evaluation is performed by `claim_boundary_checker.py` (deterministic) |
| **Setting governance scores** | Scores are computed by `evidence_completeness_scorer.py` and `governance_risk_scorer.py` |
| **Recommending outcomes** | Outcome recommendation is performed by `_apply_decision_table()` in `mech_reason.py` |
| **Triggering or overriding rules** | Rules are triggered by deterministic field comparison, not LLM judgment |
| **Sealing receipts** | Receipt sealing is performed by `ReceiptSealer` (cryptographic, deterministic) |
| **Anchoring artifacts** | Anchoring is performed by multi_anchor_verifier and external chains |
| **Approving HITL events** | HITL approval is a human signature, not an LLM output |

---

## Integration architecture

```
Evidence Bundle
      │
      ▼
MECH-REASON™ (deterministic)
  ├── claim_boundary_checker.py
  ├── evidence_completeness_scorer.py
  ├── governance_risk_scorer.py
  ├── _apply_decision_table()
  ├── _validate_state_machine()
  └── MECH_REASON_REPORT.json  ←── sealed, LLM-free
            │
            │  (read-only, post-hoc, optional)
            ▼
  [Optional LLM Advisory Adapter]
    Input:  MECH_REASON_REPORT.json (already sealed)
    Output: Human-readable narrative / HITL brief
    Writes: Advisory note only — NOT to assurance artifacts
            │
            ▼
  Human reviewer (HITL)
```

The LLM adapter **reads from** the sealed report. It never **writes to** the evidence bundle, score files, claim report, or final receipt.

---

## Data flow constraints

1. **LLM receives only sealed outputs** — it sees `MECH_REASON_REPORT.json` after sealing, never raw evidence.
2. **LLM writes to advisory namespace only** — any output is tagged `advisory_only: true`, never promoted to assurance artifacts.
3. **LLM output is not report_hash input** — the canonical `report_hash` is computed before any LLM interaction.
4. **LLM output cannot modify `recommended_outcome`** — the MechanicalGate reads `mech_reason.py` output directly, not LLM output.
5. **LLM interaction is logged separately** — any advisory call is logged in a separate `LLM_ADVISORY_LOG` with `governance_binding: false`.

---

## Preserved non-claims

These non-claims hold regardless of whether the adapter is used:

- LLM output is not final governance.
- LLM output is not official status.
- LLM output is not regulatory approval.
- LLM output is not legal compliance.
- LLM output is not certification.
- LLM output is not receipt sealing.
- LLM advisory output does not override MECH-REASON™ recommended_outcome.
- LLM advisory output does not satisfy HITL approval requirements.
- LLM advisory output is not an anchor event.

---

## When the adapter may be engaged

| Condition | Adapter permitted |
|---|---|
| `recommended_outcome = PASS` | Optional — for narrative summary |
| `recommended_outcome = SCOPE_LIMITED` | Optional — for scope clarification brief |
| `recommended_outcome = ESCALATE_TO_HITL` | Optional — to generate HITL briefing (advisory only) |
| `recommended_outcome = FAIL_CLOSED` | Not recommended — no advisory value; outcome is terminal |

---

## Implementation note

The adapter is intentionally **not implemented** in v1.2.0. This document defines its boundary so that any future implementer operates within the constitutional rule:

> MECH-REASON™ recommends mechanically. MechanicalGate decides deterministically. LLM advises, never governs.
