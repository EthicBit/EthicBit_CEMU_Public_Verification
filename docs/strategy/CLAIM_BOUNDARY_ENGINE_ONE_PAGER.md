# Claim Boundary Engine™
## One-Pager

**Product:** Claim Boundary Engine™  
**Version:** 1.0  
**Constitutional dependency:** EthicBit / CEMU v3.7.0+  
**Date:** 2026-05-12

---

## 1. What It Is

The Claim Boundary Engine™ is a **circuit breaker for AI governance claims**.

It evaluates whether a requested governance claim is supported by verified evidence artifacts, enforces Evidence Before Claims™ doctrine, and prevents overclaims before output emission or material effect.

> A claim that exceeds its evidence boundary does not reach PASS. It reaches SCOPE_LIMITED or FAIL_CLOSED.

---

## 2. Constitutional Basis

The Claim Boundary Engine operates under the EthicBit / CEMU v3.7.0+ constitutional-operational regime. It is subordinate to:

```
EthicBit / CEMU v3.7.0+
  └─ AEM v1.1 (Artifact Assurance)
       └─ AEM-EVOLVE™ (Governance Assurance)
            └─ AI-ME Gates (AI Evidence)
                 └─ Claim Boundary Engine™  ← THIS LAYER
                      └─ Fast Path
```

The Claim Boundary Engine cannot override the Constitution, AEM v1.1, or AEM-EVOLVE™. It enforces their outputs at the claim layer.

---

## 3. Why It Exists

**The problem:** AI governance systems tend toward overclaiming.

Without a boundary mechanism, systems claim:
- "Our AI is fair" — without evidence
- "Our model is auditable" — without audit artifacts
- "Our AI is compliant" — without compliance verification

The Claim Boundary Engine™ exists to make those overclaims technically impossible within the EthicBit governance infrastructure.

---

## 4. The Problem: Unsupported AI Governance Claims

Unsupported claims create:
- **Legal risk:** Regulatory bodies increasingly scrutinize AI governance claims
- **Reputational risk:** Overclaims that cannot be substantiated erode trust
- **Operational risk:** Systems that claim safety without evidence may operate outside safe bounds

The Claim Boundary Engine™ is the technical mechanism that prevents these outcomes within EthicBit-governed systems.

---

## 5. AEM v1.1 Artifact Assurance Dependency

The Claim Boundary Engine evaluates whether a requested claim is supported by evidence artifacts, **including artifacts verified through AEM v1.1 where applicable**.

This dependency is non-negotiable:
- A claim cannot reach PASS if the supporting artifact has not been verified by AEM v1.1
- A claim boundary evaluation that proceeds without AEM v1.1 verification produces an unverified boundary result
- The Claim Boundary Engine does not substitute for AEM v1.1 verification

---

## 6. How It Works

```
Claim requested
  → Identify required evidence artifacts
    → Verify artifacts through AEM v1.1
      → Evaluate claim scope against verified evidence
        → Determine claim-level ceiling
          → Compare requested claim against ceiling
            → Emit: PASS / SCOPE_LIMITED / FAIL_CLOSED
```

The claim-level ceiling is the maximum claim that the verified evidence can support. Any claim that exceeds this ceiling is blocked or scope-limited.

---

## 7. PASS / SCOPE_LIMITED / FAIL_CLOSED

| Outcome | Condition |
|---|---|
| **PASS** | Requested claim is fully within the claim-level ceiling, evidence is verified, scope matches |
| **SCOPE_LIMITED** | Requested claim exceeds some evidence scope; claim is bounded to verified scope before emission |
| **FAIL_CLOSED** | Required evidence is missing or unverified; claim cannot be supported; gate fails closed |

**SCOPE_LIMITED is not a failure.** It is an accurate, bounded claim. It prevents overclaiming while permitting valid bounded claims.

**FAIL_CLOSED is the safe default** when evidence is absent. A system that does not know its evidence status fails closed rather than emitting an unsupported claim.

---

## 8. Evidence Before Claims™

The Claim Boundary Engine operationalizes Evidence Before Claims™:

> No claim receives PASS without verified supporting evidence.

This means:
- Evidence must exist before the claim is evaluated
- Evidence must be verified by AEM v1.1 before the claim can use it
- The claim must be bounded to the verified evidence scope
- Claims cannot be upgraded by assertion — only by new evidence

---

## 9. Fast Path Consumption of Claim Boundaries

Fast Path consumes claim boundary outputs and claim-level ceilings to prevent pre-emission overclaims.

The interaction:
```
Claim Boundary Engine
  → produces claim-level ceiling
    → Fast Path inherits ceiling in canonical snapshot
      → Fast Path evaluates requested claim against ceiling before emission
        → Blocks or scope-limits claims that exceed ceiling
```

**Fast Path consumes claim boundary outputs and claim-level ceilings to prevent pre-emission overclaims.**

This means the Claim Boundary Engine runs before Fast Path, and Fast Path enforces the Claim Boundary Engine's outputs at runtime.

---

## 10. Example Claim Evaluation

**Scenario:** An AI system requests to emit the claim "our AI is fully fair and compliant."

```
Claim requested: "fully fair and compliant"
Required evidence:
  - AI-ME-02 Bias/Fairness evidence artifact → status: PENDING
  - AI-ME-12 Claim Boundary enforcement log → status: PENDING

AEM v1.1 verification:
  - artifact_verified: false (AI-ME-02 not yet executed)

Claim Boundary Engine evaluation:
  - claim_level_ceiling: SCOPE_LIMITED (no verified fairness evidence)
  - requested claim exceeds ceiling

Outcome: SCOPE_LIMITED
Permitted claim: "AEM-EVOLVE v3.0 formalizes our Mechanical Ethics Assurance
                  infrastructure; AI-ME fairness evidence is roadmap (v3.1)"
Blocked claim: "fully fair and compliant"
```

---

## 11. Legal / Reputation Risk Reduction

By enforcing claim boundaries, the Claim Boundary Engine™ reduces:

- **Regulatory exposure:** AI governance claims are bounded to verifiable evidence
- **False advertising risk:** Marketing claims about AI ethics cannot exceed technical evidence
- **Audit exposure:** Governance records show that claims were evidence-bound at time of emission
- **Liability risk:** Overclaims that cause harm cannot be made through the governed system

This risk reduction is structural, not advisory. The mechanism prevents the overclaim at the technical layer.

---

## 12. What It Does Not Claim

The Claim Boundary Engine does not provide:
- Legal advice
- Regulatory approval
- External certification
- Automatic AI ethics compliance
- Universal claim coverage

It is a technical enforcement mechanism within the EthicBit governance infrastructure.

---

## 13. Summary

| Property | Value |
|---|---|
| Category | Claim Enforcement Layer |
| Position | After AI-ME Gates, before Fast Path |
| Doctrine | Evidence Before Claims™ |
| Artifact dependency | AEM v1.1 verification |
| Outputs | PASS / SCOPE_LIMITED / FAIL_CLOSED |
| Fast Path integration | Claim-level ceiling consumed by Fast Path |
| Safe default | FAIL_CLOSED when evidence is absent |
| Analogy | Circuit breaker for AI governance claims |

**The Claim Boundary Engine™ binds AI governance claims to evidence, scope, target, hashes, artifact verification status and closure conditions.**

---

*Claim Boundary Engine™ One-Pager v1.0 — EthicBit / CEMU v3.7.0+ — 2026-05-12*
