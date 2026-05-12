# Fast Path — Deterministic Pre-Execution Gating with Snapshot Inheritance

**Document type:** Technical Specification  
**Version:** 1.0  
**Status:** `SPECIFICATION_AND_SCAFFOLD_RELEASE`  
**Constitutional dependency:** EthicBit / CEMU v3.7.0+  
**Artifact assurance:** AEM v1.1  
**Date:** 2026-05-12

---

## 1. Overview

Fast Path is a **deterministic pre-execution enforcement layer** within the EthicBit / AEM-EVOLVE governance stack.

It operates at runtime or pre-emission, consuming a signed canonical snapshot to evaluate enforcement conditions and emit a verdict **before** output emission or material effect.

**Fast Path is not a full governance system.** It is a specialized enforcement layer that inherits pre-computed state from the complete governance stack and enforces it at low latency.

---

## 2. Constitutional Position

Fast Path is subordinated to the EthicBit / CEMU v3.7.0+ constitutional-operational regime:

```
EthicBit / CEMU v3.7.0+ (Constitutional Regime)
  └─ AEM v1.1 (Artifact Assurance)
       └─ AEM-EVOLVE™ (Governance Assurance)
            └─ AI-ME Gates (AI Evidence)
                 └─ Claim Boundary Engine™ (Claim Enforcement)
                      └─ Fast Path  ← THIS LAYER
                           └─ Triple Anchor
                                └─ Strong Closure
                                     └─ v4.0 External Validation
```

**Fast Path cannot:**
- Override AEM v1.1 artifact verification failure
- Upgrade failed AI-ME evidence
- Replace AEM-EVOLVE™ governance outcome
- Replace Triple Anchor
- Replace Strong Closure
- Emit PASS for a prohibited action or a claim that exceeds the claim-level ceiling

---

## 3. What Fast Path Evaluates

At each enforcement tick, Fast Path evaluates:

| Check | Description |
|---|---|
| Snapshot validity | Is the inherited canonical snapshot signed and valid? |
| Snapshot freshness | Is `snapshot_age_ms` within `max_tick_elapsed_ms`? |
| Claim-level ceiling | Does the requested claim fall within the inherited ceiling? |
| Authorized capabilities | Is the requested operation within the authorized capability set? |
| Prohibited actions | Does the requested operation match any prohibited action pattern? |
| Constitutional equivalence | Is the operation consistent with the constitutional-operational regime? |
| Pre-execution verdict | What verdict should be emitted before output/action? |
| Output emission boundary | Should the output be emitted, blocked, or scope-limited? |

---

## 4. Snapshot Inheritance

Fast Path inherits its enforcement state from a **signed canonical snapshot**. This snapshot contains:

- `claim_level_ceiling` — maximum allowed claim derived from Claim Boundary Engine
- `authorized_capabilities` — capability set authorized by the governance stack
- `prohibited_actions` — patterns that must be blocked
- `constitutional_equivalence_hash` — hash reference to constitutional-operational state
- `aem_artifact_assurance_summary` — AEM v1.1 verification summary
- `ai_me_gate_outcomes` — summary of AI-ME gate outcomes (not full recomputation)
- `snapshot_timestamp` — when the snapshot was created
- `snapshot_signature` — cryptographic signature over snapshot content

The snapshot is created by the full governance stack and signed. Fast Path **does not recompute** Triple Anchor, Strong Closure, or complete AI-ME evidence per tick. It operates on inherited state.

---

## 5. Enforcement Verdicts

| Verdict | Meaning |
|---|---|
| **PASS** | Operation is within authorized scope and claim ceiling; emit |
| **BLOCK** | Operation matches prohibited action pattern; do not emit |
| **SCOPE_LIMITED** | Requested claim exceeds ceiling; emit with mandatory scope qualifier |
| **DEGRADED** | Snapshot is stale (exceeds `max_tick_elapsed_ms`) but enforcement proceeds with degraded confidence |
| **NOT_VERIFIABLE** | Snapshot is missing or unsigned; enforcement cannot proceed; fail safe |
| **FAIL_CLOSED** | Required condition fails; do not emit; record enforcement event |

---

## 6. Mandatory Rules

```
Fast Path cannot override AEM v1.1 artifact verification failure.
Fast Path cannot upgrade failed AI-ME evidence.
Fast Path cannot replace AEM-EVOLVE™ governance outcome.
Fast Path cannot replace Triple Anchor.
Fast Path cannot replace Strong Closure.
Fast Path must fail closed or block if a prohibited action is detected.
Fast Path must scope-limit or block if requested claim exceeds claim-level ceiling.
Fast Path must not claim full-system validation latency.
```

These rules are constitutional. They are not optional.

---

## 7. Latency Considerations

Fast Path is designed for low-latency enforcement targets (e.g., sub-15ms where separately measured and evidenced). This latency applies only to the Fast Path enforcement evaluation itself — not to the full governance stack.

**Important non-claim:** The full Triple Anchor, Strong Closure, and complete AI-ME evidence execution do NOT operate within Fast Path latency. Only the specialized pre-emission enforcement layer does.

Latency claims for Fast Path must be:
- Separately measured (not inferred)
- Evidenced in a dedicated benchmark artifact
- Scope-qualified to Fast Path enforcement only

---

## 8. Fail-Safe Behavior

Fast Path applies fail-safe behavior in all ambiguous states:

- Missing snapshot → NOT_VERIFIABLE → do not emit
- Unsigned snapshot → NOT_VERIFIABLE → do not emit  
- Stale snapshot beyond `max_tick_elapsed_ms` → DEGRADED (if configured) or FAIL_CLOSED
- Prohibited action detected → BLOCK or FAIL_CLOSED
- Claim exceeds ceiling with no available scope-limited form → FAIL_CLOSED

Fail-safe means: when in doubt, do not emit. Record the enforcement event. Report the condition.

---

## 9. Integration Points

Fast Path integrates with:

| Layer | Integration |
|---|---|
| Claim Boundary Engine™ | Inherits claim-level ceiling from claim boundary snapshot |
| AEM v1.1 | Inherits artifact verification summary; cannot override AEM v1.1 failures |
| AI-ME-06 | Tool-call authorization enforcement before emission |
| AI-ME-08 | HITL requirement enforcement before high-risk output emission |
| AI-ME-12 | Claim boundary enforcement log reference |
| Triple Anchor | Does not replace; anchoring occurs outside Fast Path |
| Strong Closure | Does not replace; closure evaluation occurs outside Fast Path |

---

## 10. Claim

This document documents and scaffolds the Fast Path for deterministic pre-execution gating with snapshot inheritance, including support for low-latency enforcement targets such as sub-15 ms operation where separately measured and evidenced.

---

## 11. Non-Claims

This PR does not claim that the full Triple Anchor, Strong Closure, or complete AI-ME evidence execution operates in milliseconds. It only covers the specialized Fast Path runtime/pre-emission enforcement layer.

This document does not claim:
- Production readiness
- External validation
- Cybersecurity certification
- Universal enforcement coverage
- That Fast Path subsumes the complete governance stack

---

*Fast Path — Deterministic Pre-Execution Gating v1.0 — EthicBit / CEMU v3.7.0+ — 2026-05-12*
