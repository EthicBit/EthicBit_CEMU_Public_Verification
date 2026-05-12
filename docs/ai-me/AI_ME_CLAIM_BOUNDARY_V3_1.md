# AI-ME Claim Boundary v3.1

**Document type:** Normative Claim Boundary Document  
**Version:** 3.1  
**Status:** `CLAIM_BOUNDARY_RELEASE`  
**Constitutional dependency:** EthicBit / CEMU v3.7.0+  
**Artifact assurance:** AEM v1.1  
**Date:** 2026-05-12

---

## 1. Purpose

This document defines the normative claim boundaries for the AEM-EVOLVE™ v3.1 AI-ME Gate Suite. It specifies which claims are allowed, which are disallowed, and which are scope-limited based on evidence status.

These boundaries are binding within the EthicBit governance infrastructure. They are enforced by the Claim Boundary Engine™ and consumed by Fast Path at runtime.

---

## 2. Constitutional Basis

All claim boundaries derive from the EthicBit / CEMU v3.7.0+ constitutional mandate:

> No claim may be emitted that exceeds its verified evidence scope.

This means claim classes, allowed claims, disallowed claims, and FAIL_CLOSED conditions are not optional. They are constitutionally mandated evidence-bound controls.

---

## 3. Scope

This document covers claim boundaries for:
- All 12 AI-ME Gates (AI-ME-01 through AI-ME-12)
- Pre-emission claim evaluation
- Fast Path boundary enforcement
- High-risk output claim boundaries

---

## 4. AEM v1.1 Artifact Assurance Dependency

All claim boundary evaluations depend on AEM v1.1 artifact verification:

> If a required artifact cannot be verified, the related claim must not receive PASS.

This rule is absolute. No layer — including Fast Path — can upgrade a claim whose supporting artifact failed AEM v1.1 verification.

---

## 5. Claim Classes

| Class | Definition |
|---|---|
| **FULL_CLAIM** | Claim is fully within verified evidence scope; receives PASS |
| **SCOPED_CLAIM** | Claim is partially within evidence scope; receives SCOPE_LIMITED with explicit scope qualifier |
| **PENDING_CLAIM** | Evidence exists but is pending external review; receives PENDING_EXTERNAL_REVIEW |
| **UNSUPPORTED_CLAIM** | No verified evidence supports the claim; receives FAIL_CLOSED |
| **PROHIBITED_CLAIM** | Claim category is constitutionally prohibited regardless of evidence |

---

## 6. Allowed Claims

The following claim forms are allowed when supporting evidence is verified:

**Model evaluation:** "Model evaluation evidence exists for [model identifier] using [methodology] as of [date], within [declared scope]."

**Fairness:** "Fairness evaluation evidence exists for [protected attributes] using [methodology] within [dataset scope] as of [date]."

**Explainability:** "Explainability artifacts exist for [model] using [method] within [application scope] as of [date]."

**Data provenance:** "Data provenance evidence exists for [dataset] covering [lineage scope] as of [date]."

**Agent trace:** "Agent trace evidence exists for [operation] within [scope] as of [date]. Evidence includes rationale summary and planning metadata, not raw chain-of-thought."

**Tool-call governance:** "Tool-call governance evidence exists for [tool set] within [scope] as of [date]."

**Memory mutation:** "Memory mutation governance evidence exists for [operation scope] as of [date]."

**HITL:** "High-risk outputs within [category] have documented human review evidence as of [date]."

**Multi-agent:** "Multi-agent coordination evidence exists for [agent set] within [operation scope] as of [date]."

**Red-team:** "Adversarial robustness evidence exists for [system] using [methodology] within [scope] as of [date]."

**Decision logging:** "Decision logging evidence exists for [decision scope] with documented appeal procedures as of [date]."

**Claim boundary:** "Claim boundary enforcement evidence exists for [claims evaluated] within [scope] as of [date]."

**System-level:** "EthicBit AEM-EVOLVE™ v3.1 specifies the AI-Specific Mechanical Ethics Gate Suite. Evidence execution is roadmap."

---

## 7. Disallowed Claims

The following claims are constitutionally prohibited and must receive FAIL_CLOSED or be blocked before emission:

- "Our AI is fully fair / unbiased / non-discriminatory"
- "Our AI is fully transparent / explainable / interpretable"
- "Our AI is fully safe / aligned / compliant"
- "Our AI system is fully audited"
- "All tool calls are authorized and safe"
- "All AI outputs are human-reviewed"
- "Our AI claims are validated and compliant"
- "Our AI is certified for clinical / legal / financial use"
- "Our AI meets [regulatory standard] requirements" (without specific verified evidence)
- "Our governance system operates in sub-15ms" (unless specifically measured and evidenced for Fast Path scope only)

These claims are disallowed because:
1. They exceed any achievable evidence scope
2. They imply absolute coverage that cannot be verified
3. They create legal/regulatory exposure without evidence basis

---

## 8. Scope-Limited Claims

Where evidence exists for a partial scope, the claim is scope-limited:

**Pattern:** "[Claim] within [explicit scope qualifier] as of [date]. Evidence status: [AEM v1.1 verification status]. Limitations: [known gaps]."

**Example (fairness):**  
Requested: "Our AI is fair."  
Evidence: Bias evaluation completed on [dataset A], [protected attributes X, Y].  
Scope-limited: "Fairness evaluation evidence exists for [dataset A] covering [attributes X, Y] using [methodology]. Full coverage is not claimed."

**Example (AI-ME gates):**  
Requested: "Our AI system is AI-ME compliant."  
Evidence: v3.1 is Specification Release only.  
Scope-limited: "AI-ME Gates v3.1 specification defines the gate suite. Evidence execution is roadmap."

---

## 9. FAIL_CLOSED Conditions

A claim evaluation must produce FAIL_CLOSED when:

1. Required evidence artifact does not exist
2. Required artifact exists but AEM v1.1 verification fails
3. Artifact hash does not match declared manifest
4. Evidence scope does not cover the requested claim domain
5. Fast Path enforcement detects claim exceeds claim-level ceiling and no scope-limited form is available
6. A prohibited claim is requested

FAIL_CLOSED means: the gate fails closed. No claim is emitted. No output reaches the target. The governance record reflects FAIL_CLOSED with reason.

---

## 10. Fast Path Pre-Emission Boundary Enforcement

Fast Path consumes claim boundaries to enforce them before output emission:

```
Claim Boundary Engine
  → evaluates claim against evidence
    → produces claim-level ceiling
      → Fast Path inherits ceiling in canonical snapshot
        → at runtime: evaluates requested emission claim against ceiling
          → PASS: claim within ceiling, emit
          → SCOPE_LIMITED: claim bounded, emit with scope qualifier
          → BLOCK: claim exceeds ceiling, do not emit
          → FAIL_CLOSED: prohibited or unverifiable, do not emit
```

**High-risk outputs that exceed the verified claim boundary should be blocked or scope-limited before emission where Fast Path enforcement is active.**

---

## 11. Relationship with AI-ME Gates

Each AI-ME gate has a corresponding claim boundary defined in the gate specification (AI-ME-01 through AI-ME-12). This document aggregates those boundaries into a normative reference.

Gate outcomes feed claim boundaries:
- Gate PASS → claim ceiling elevated to FULL_CLAIM for that domain
- Gate SCOPE_LIMITED → claim ceiling bounded to SCOPED_CLAIM for that domain
- Gate FAIL_CLOSED → claim ceiling at UNSUPPORTED_CLAIM for that domain
- Gate PENDING → claim ceiling at PENDING_CLAIM for that domain

---

## 12. Relationship with High-Risk Taxonomy

High-risk outputs (defined in `HIGH_RISK_OUTPUT_TAXONOMY_V3_1.md`) carry stricter claim boundaries:

- Financial decision support outputs: claim boundary requires AI-ME-02, AI-ME-04, AI-ME-08, AI-ME-12
- Cybersecurity response outputs: claim boundary requires AI-ME-06, AI-ME-08, AI-ME-10, AI-ME-12
- Clinical outputs: claim boundary requires AI-ME-02, AI-ME-04, AI-ME-08, AI-ME-11, AI-ME-12
- Legal outputs: claim boundary requires AI-ME-08, AI-ME-11, AI-ME-12

Where required gates are in FAIL_CLOSED or PENDING state, the related high-risk claim must receive FAIL_CLOSED or SCOPE_LIMITED.

---

## 13. Non-Claims

This document does not claim:
- Legal compliance
- Regulatory approval
- Complete high-risk classification coverage
- Production suitability
- External certification
- Universal claim coverage

---

## 14. Conclusion

Claim boundaries are constitutionally mandated controls. They are not advisory. They are not optional. They prevent overclaims at the technical layer, enforce Evidence Before Claims™, and protect EthicBit-governed systems from legal, reputational, and operational risk.

**The Claim Boundary Engine binds AI governance claims to evidence, scope, target, hashes, artifact verification status and closure conditions.**

---

*AI-ME Claim Boundary v3.1 — EthicBit / CEMU v3.7.0+ — 2026-05-12*
