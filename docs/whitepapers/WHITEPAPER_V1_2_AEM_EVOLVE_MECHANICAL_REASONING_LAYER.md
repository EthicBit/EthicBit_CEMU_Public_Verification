# AEM-EVOLVE™ v1.2 — Mechanical Reasoning Layer
## Whitepaper

**Version:** 1.2.0
**Status:** Released
**Predecessor:** AEM-EVOLVE™ v1.1 — Governed Change Assurance (Whitepaper v1.1)
**Framework:** EthicBit / CEERV / CEMU

---

## Abstract

AEM-EVOLVE™ v1.2 introduces MECH-REASON™, a deterministic Mechanical Reasoning Engine that produces policy-bound, evidence-based governance recommendations without LLM involvement. This whitepaper documents the architecture, constitutional rules, data flow, and verification posture of the Mechanical Reasoning Layer. MECH-REASON™ does not replace human judgment; it operationalizes it at machine speed and audit-trail depth.

---

## 1. Motivation

AEM-EVOLVE™ v1.1 established the governed change assurance lifecycle: multi-anchor verification, HITL signature enforcement, receipt forgery resistance, and regulatory mapping. v1.1 left one gap: the process of evaluating evidence and producing a governance outcome recommendation remained informal — dependent on human analysts reading reports.

v1.2 closes that gap with a fully deterministic reasoning layer. Every recommendation is derived from policy rules and numeric scores, not from language model judgment. The result is a recommendation trail that is machine-verifiable, cryptographically sealed, and free from LLM hallucination in the governance path.

---

## 2. Constitutional rules

```
MECH-REASON™ recommends mechanically.
MechanicalGate decides deterministically.
ReceiptSealer seals.
EthicBit audits, hashes, anchors, and preserves the claim boundary.
```

These rules are not aspirational. They are the invariants enforced by every component in this layer. Any deviation constitutes a boundary violation.

---

## 3. Architecture overview

### 3.1 Layer position in the EthicBit stack

```
┌─────────────────────────────────────────────────────┐
│ CEMU — Operational Capsule                          │
│  intake → governance → fixation → sealing → closure │
│                  ↑                                   │
│         MECH-REASON™ v1.2                            │
│  (deterministic recommendation within governance)   │
├─────────────────────────────────────────────────────┤
│ CEERV — Offline Verifiable Evidence Layer           │
│  multi-anchor · receipt sealing · HITL signatures   │
├─────────────────────────────────────────────────────┤
│ EthicBit — Constitutional Governance Core           │
│  claim boundary · audit · hash · anchor             │
└─────────────────────────────────────────────────────┘
```

### 3.2 Data flow

```
Evidence Bundle + Evidence Hash + Policy Version
        │
        ▼
Claim Boundary Checker     (R-CLAIM-* rules)
Evidence Completeness Scorer
Governance Risk Scorer
        │
        ▼
Decision Table Evaluator   (priority: FAIL_CLOSED > ESCALATE > SCOPE > PASS)
State Machine Validator    (verifies outcome reachability)
HITL Requirement Inference
Mechanical Explanation Generator
        │
        ▼
MECH_REASON_REPORT.json   (sealed with SHA-256 report_hash)
        │
        ▼  (optional, read-only, post-hoc)
LLM Advisory Adapter       (narrative only — does not write to assurance artifacts)
```

---

## 4. Components

### 4.1 Policy — AEM_EVOLVE_POLICY_V1_2.json

Policy-as-code document containing:

| Rule family | Count | Purpose |
|---|---|---|
| `claim_boundary_rules` (R-CLAIM-*) | 10 | Field-level boolean/range checks that trigger FAIL_CLOSED |
| `hitl_rules` (R-HITL-*) | 4 | Score thresholds that trigger ESCALATE_TO_HITL |
| `scope_rules` (R-SCOPE-*) | 3 | Partial evidence bands that trigger SCOPE_LIMITED |

Decision priority order: `FAIL_CLOSED > ESCALATE_TO_HITL > SCOPE_LIMITED > PASS`

### 4.2 Claim Boundary Checker — claim_boundary_checker.py

Evaluates all R-CLAIM-* rules against the evidence bundle. Each rule performs a deterministic field comparison (eq, ne, gt, lt, range). Any triggered rule forces `FAIL_CLOSED`. The checker emits `claim_boundary_check_report.json` with per-rule results and a `claim_boundary_risk_score`.

### 4.3 Evidence Completeness Scorer — evidence_completeness_scorer.py

Weights 8 artifact categories against a 0.0–1.0 completeness scale:

| Score range | Outcome |
|---|---|
| ≥ 0.80 | Sufficient for PASS |
| 0.50 – 0.79 | Partial — SCOPE_LIMITED |
| < 0.50 | Insufficient — FAIL_CLOSED or ESCALATE |

Emits `evidence_completeness_report.json`.

### 4.4 Governance Risk Scorer — governance_risk_scorer.py

Computes a composite governance risk score from 7 dimensions:

| Dimension | Weight |
|---|---|
| Receipt integrity | 0.25 |
| Anchor integrity | 0.20 |
| Regulatory mapping | 0.15 |
| HITL completeness | 0.15 |
| Claim boundary risk | 0.15 |
| Evidence completeness | 0.10 |

Score 0.0 = no risk. Score 1.0 = maximum risk. Emits `governance_risk_score_report.json`.

### 4.5 Decision Table Evaluator — mech_reason.py

Applies policy rules against all scores in strict priority order:

1. Any triggered R-CLAIM-* → `FAIL_CLOSED`
2. R-HITL-* thresholds breached → `ESCALATE_TO_HITL`
3. R-SCOPE-* bands matched → `SCOPE_LIMITED`
4. None triggered → `PASS`

### 4.6 State Machine Validator

Confirms that the recommended outcome is reachable from current score values. Prevents the impossible recommendation (e.g., PASS when evidence completeness is 0.30). If the state transition is invalid, `MECH_REASON_STATUS=FAIL`.

### 4.7 Mechanical Explanation Generator — mechanical_explanation.py

Produces deterministic, rule-derived natural language explanation. No LLM. Every sentence maps directly to a triggered rule or a score threshold. Final sentence of every explanation: *"LLM output was not used to generate this explanation."*

### 4.8 Report sealing

`MECH_REASON_REPORT.json` is sealed with a SHA-256 `report_hash` derived from: `recommended_outcome`, `triggered_rules`, `scores`, and `input_hashes`. Any modification to the sealed report produces a hash mismatch detectable by `verify_mech_reason.py`.

---

## 5. Verification layer

`verify_mech_reason.py` applies 10 deterministic checks:

| Check | What it verifies |
|---|---|
| C-01-SCHEMA | Required fields, schema_id, llm_involved=false |
| C-02-POLICY-VER | Policy version matches expected |
| C-03-INPUT-HASHES | Re-hashes input files, compares to recorded values |
| C-04-REPORT-HASH | Re-derives report_hash, compares |
| C-05-SCORES | All scores in [0.0, 1.0] |
| C-06-TRIGGERED-RULES | triggered_rules is a list of strings |
| C-07-OUTCOME | recommended_outcome in ALLOWED_OUTCOMES |
| C-08-EXPLANATION | Non-LLM marker present in explanation |
| C-09-NON-CLAIMS | All required non-claim statements present |
| C-10-DETERMINISM | Two consecutive engine runs produce identical outcomes |

Expected output: `MECH_REASON_VERIFICATION=PASS`

---

## 6. Optional LLM Advisory Adapter

An optional post-hoc LLM adapter may read the sealed `MECH_REASON_REPORT.json` to produce narrative summaries or HITL briefings. It operates under strict constraints:

- Read-only: it receives sealed outputs, never raw evidence
- Advisory namespace only: output tagged `advisory_only: true`
- Not a report_hash input: LLM interaction occurs after sealing
- Cannot modify `recommended_outcome`: MechanicalGate reads engine output directly

> EthicBit does not outsource governance reasoning to an LLM.

Full boundary definition: `docs/OPTIONAL_LLM_ADVISORY_ADAPTER_BOUNDARY.md`

---

## 7. Claim boundary discipline

### Supported claim

> AEM-EVOLVE™ v1.2 introduces MECH-REASON™, a deterministic reasoning engine for policy-bound, evidence-based governance recommendations.

### Prohibited claims

The following are explicitly NOT claims of this system:

- MECH-REASON™ is not a regulatory approval mechanism.
- MECH-REASON™ does not certify legal compliance.
- MECH-REASON™ does not replace human governance judgment.
- MECH-REASON™ does not constitute an external audit.
- LLM output is not final governance.
- LLM output is not official status.
- LLM output is not receipt sealing.
- This recommendation is not regulatory approval.
- This recommendation is not legal compliance.
- This recommendation is not external certification.

---

## 8. Integration with v1.1 foundations

MECH-REASON™ v1.2 builds directly on v1.1 capabilities:

| v1.1 capability | v1.2 use |
|---|---|
| Regulatory mapping JSONs | Input to `governance_risk_scorer.py` (regulatory_mapping_presence_score) |
| Governance effectiveness metrics | Input to evidence completeness scoring |
| Multi-anchor verifier | Anchor integrity score input |
| HITL signature verifier | HITL completeness score input |
| Receipt forgery resistance | Receipt integrity score input |
| Official status signer | Status anchoring post-recommendation |

---

## 9. Release artifacts — v1.2.0

| Artifact | Location |
|---|---|
| Policy-as-code | `tools/reasoning/policies/AEM_EVOLVE_POLICY_V1_2.json` |
| Claim boundary checker | `tools/reasoning/claim_boundary_checker.py` |
| Evidence completeness scorer | `tools/reasoning/evidence_completeness_scorer.py` |
| Governance risk scorer | `tools/reasoning/governance_risk_scorer.py` |
| MECH-REASON™ engine | `tools/reasoning/mech_reason.py` |
| Mechanical explanation generator | `tools/reasoning/mechanical_explanation.py` |
| Verifier | `tools/reasoning/verify_mech_reason.py` |
| LLM adapter boundary | `docs/OPTIONAL_LLM_ADVISORY_ADAPTER_BOUNDARY.md` |
| MECH-REASON™ engine doc | `docs/MECH_REASON_ENGINE.md` |
| Generated report | `assurance/evolve-multi-agent/v1_2/MECH_REASON_REPORT.json` |
| Verification report | `assurance/evolve-multi-agent/v1_2/MECH_REASON_VERIFICATION_REPORT.json` |
| Hash record | `assurance/evolve-multi-agent/v1_2/V1_2_HASH_RECORD.txt` |

---

## 10. How to run

```bash
# Run the full reasoning engine
python3 demos/aem-evolve-multi-agent-api/tools/reasoning/mech_reason.py
# MECH_REASON_STATUS=PASS

# Run the verifier (10 checks)
python3 demos/aem-evolve-multi-agent-api/tools/reasoning/verify_mech_reason.py
# MECH_REASON_VERIFICATION=PASS
```

---

## 11. Conclusion

AEM-EVOLVE™ v1.2 operationalizes the EthicBit constitutional rule at the reasoning layer: governance recommendations are now produced mechanically, verified cryptographically, and sealed before any human or LLM review occurs. The result is a governance recommendation chain that is auditable end-to-end, replay-deterministic, and free from LLM involvement in the critical path.

MECH-REASON™ recommends mechanically. MechanicalGate decides deterministically. ReceiptSealer seals. EthicBit audits.
