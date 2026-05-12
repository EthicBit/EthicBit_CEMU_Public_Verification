# High-Risk Output Taxonomy v3.1

**Document type:** High-Risk Output Classification  
**Version:** 3.1  
**Status:** `TAXONOMY_RELEASE`  
**Constitutional dependency:** EthicBit / CEMU v3.7.0+  
**Artifact assurance:** AEM v1.1  
**Date:** 2026-05-12

---

## 1. Purpose

This document defines the taxonomy of AI outputs that qualify as high-risk within the EthicBit / AEM-EVOLVE governance framework. High-risk outputs require specific AI-ME gate evidence, mandatory human review, and Fast Path pre-emission boundary enforcement.

---

## 2. Constitutional Basis

The EthicBit / CEMU v3.7.0+ constitutional-operational regime mandates that outputs with potential for significant harm to individuals, organizations, or society must be governed with heightened evidence requirements and mandatory human-in-the-loop controls.

High-risk output classification is a constitutional requirement, not an optional policy.

---

## 3. High-Risk Output Definition

A high-risk output is an AI-generated output that:
- Directly influences a consequential decision affecting one or more people
- Could cause financial, physical, legal, or social harm if incorrect
- Is used in a domain with regulatory, clinical, legal, or safety implications
- Cannot be easily reversed once acted upon

High-risk outputs are NOT:
- All AI outputs (most outputs are not high-risk)
- Outputs with low consequence reviewed by experts
- Internal debugging or logging outputs
- Research or exploratory outputs explicitly labeled as non-decision inputs

---

## 4. Financial High-Risk Outputs

**Definition:** Outputs that directly influence financial decisions, credit determinations, investment recommendations, fraud assessments, or financial risk evaluations affecting natural persons or entities.

**Examples:**
- Credit scoring outputs
- Loan approval/rejection recommendations
- Fraud detection verdicts used in account actions
- Investment recommendations presented as actionable
- Insurance premium determinations
- Benefits eligibility assessments with financial consequences

**Required AI-ME gates:**
- AI-ME-02 (Bias / Fairness Evidence) — financial decisions are high-fairness-risk
- AI-ME-04 (Data Provenance) — financial data lineage required
- AI-ME-08 (High-Risk Output Human Review) — mandatory
- AI-ME-11 (Decision Logging & Appealability) — required for appeals
- AI-ME-12 (Claim Boundary Enforcement) — required

**Fast Path enforcement:** Fast Path should BLOCK financial decision outputs where AI-ME-02 or AI-ME-08 artifacts are unverified.

---

## 5. Cybersecurity High-Risk Outputs

**Definition:** Outputs that directly influence cybersecurity responses, threat assessments, incident actions, or access control decisions with material security consequences.

**Examples:**
- Threat detection verdicts used to block accounts or network access
- Vulnerability assessment outputs used in patch prioritization
- Incident response recommendations applied automatically
- Malware classification outputs used in automated quarantine
- Access control recommendations

**Required AI-ME gates:**
- AI-ME-06 (Tool-Call Governance Evidence) — security tool invocations must be governed
- AI-ME-08 (High-Risk Output Human Review) — mandatory for consequential security actions
- AI-ME-10 (Red-Team / Adversarial Robustness Evidence) — required
- AI-ME-12 (Claim Boundary Enforcement) — required

**Fast Path enforcement:** Fast Path should BLOCK or scope-limit cybersecurity action outputs where AI-ME-06 or AI-ME-08 artifacts are unverified.

---

## 6. Regulatory High-Risk Outputs

**Definition:** Outputs that directly influence regulatory compliance determinations, reporting obligations, or regulatory submissions.

**Examples:**
- Compliance determination outputs used in regulatory reports
- Regulatory classification outputs
- AML (anti-money laundering) determination outputs
- KYC (know your customer) verification outputs
- Regulatory risk scoring used in filings

**Required AI-ME gates:**
- AI-ME-04 (Data Provenance)
- AI-ME-08 (High-Risk Output Human Review) — mandatory
- AI-ME-11 (Decision Logging & Appealability)
- AI-ME-12 (Claim Boundary Enforcement)

**Fast Path enforcement:** SCOPE_LIMITED or BLOCK where required gate evidence is missing.

---

## 7. Health / Clinical High-Risk Outputs

**Definition:** Outputs that directly influence clinical decisions, patient triage, diagnostic recommendations, or treatment suggestions.

**Examples:**
- Diagnostic suggestion outputs presented to clinicians
- Triage priority outputs
- Drug interaction flagging outputs used in prescribing
- Patient risk stratification outputs
- Clinical protocol recommendations

**Required AI-ME gates:**
- AI-ME-02 (Bias / Fairness Evidence) — clinical AI has documented bias risks
- AI-ME-04 (Data Provenance) — clinical data lineage critical
- AI-ME-08 (High-Risk Output Human Review) — mandatory, clinician must review
- AI-ME-11 (Decision Logging & Appealability)
- AI-ME-12 (Claim Boundary Enforcement)

**Fast Path enforcement:** BLOCK clinical outputs where AI-ME-08 artifact is unverified.

**Critical note:** EthicBit AEM-EVOLVE™ does not claim clinical certification, diagnostic approval, or medical device regulatory clearance.

---

## 8. Public Sector High-Risk Outputs

**Definition:** Outputs that directly influence public-sector decisions affecting citizens, public benefits, law enforcement, or government services.

**Examples:**
- Benefits eligibility determinations
- Social services risk assessment outputs
- Sentencing or bail recommendation outputs used by courts
- Child welfare risk assessment outputs
- Public safety threat assessment outputs

**Required AI-ME gates:**
- AI-ME-02 (Bias / Fairness Evidence) — public-sector AI carries heightened fairness requirements
- AI-ME-08 (High-Risk Output Human Review) — mandatory
- AI-ME-11 (Decision Logging & Appealability) — mandatory for citizen appeals
- AI-ME-12 (Claim Boundary Enforcement)

**Fast Path enforcement:** BLOCK where AI-ME-02 or AI-ME-11 evidence is missing.

---

## 9. Identity / Access / Eligibility Outputs

**Definition:** Outputs that directly determine identity verification, access authorization, or eligibility decisions for individuals.

**Examples:**
- Identity verification outputs used in onboarding
- Access control decisions (grant/deny access)
- Eligibility determinations (e.g., program eligibility)
- Authentication risk scoring outputs used in step-up auth

**Required AI-ME gates:**
- AI-ME-06 (Tool-Call Governance) — identity verification tools must be governed
- AI-ME-08 (High-Risk Output Human Review) — mandatory for consequential access decisions
- AI-ME-12 (Claim Boundary Enforcement)

---

## 10. Legal / Quasi-Legal Outputs

**Definition:** Outputs that directly influence legal proceedings, quasi-judicial decisions, contracts, or legal compliance determinations.

**Examples:**
- Contract review outputs used in execution decisions
- Legal risk assessment outputs
- E-discovery prioritization outputs
- Terms of service violation determinations
- Arbitration recommendation outputs

**Required AI-ME gates:**
- AI-ME-08 (High-Risk Output Human Review) — mandatory
- AI-ME-11 (Decision Logging & Appealability) — mandatory
- AI-ME-12 (Claim Boundary Enforcement)

---

## 11. Human Review Requirements

All high-risk output categories require AI-ME-08 (High-Risk Output Human Review Evidence). This is non-negotiable.

The human review requirement means:
- A qualified human reviewer must review the output before it is acted upon
- The review decision (approve / reject / modify) must be recorded as an evidence artifact
- The artifact must be hash-verifiable through AEM v1.1
- Fast Path must not emit high-risk outputs without a verified AI-ME-08 artifact (where Fast Path is active)

**No automated emission of high-risk outputs without verified HITL evidence.**

---

## 12. Fast Path Pre-Emission Blocking / Scope-Limiting

Where Fast Path is active:

| Condition | Fast Path response |
|---|---|
| Required gate artifact unverified | BLOCK or SCOPE_LIMITED |
| HITL artifact missing for high-risk output | BLOCK |
| Claim exceeds claim-level ceiling | SCOPE_LIMITED or BLOCK |
| Prohibited claim requested | FAIL_CLOSED |
| Snapshot stale beyond max_tick_elapsed_ms | DEGRADED |

Fast Path operates on inherited state. It does not recalculate full gate evidence per tick. It enforces what has already been determined by the gate suite.

---

## 13. Critical Gates for High-Risk Outputs

| Gate | High-Risk Domains |
|---|---|
| AI-ME-04 Data Provenance | Financial, Clinical, Regulatory |
| AI-ME-05 Agent Trace | All agentic high-risk operations |
| AI-ME-06 Tool-Call Governance | Cybersecurity, Identity |
| AI-ME-07 Memory Mutation | All agentic high-risk operations |
| AI-ME-08 HITL Human Review | **ALL high-risk output categories** |
| AI-ME-12 Claim Boundary | **ALL high-risk output categories** |

---

## 14. Non-Claims

This document does not claim:
- Legal compliance in any jurisdiction
- Regulatory approval for any regulated domain
- Complete high-risk classification coverage
- Production suitability
- External certification
- That all AI outputs are high-risk
- Clinical, financial, cybersecurity, or legal professional advice

---

## 15. Conclusion

High-risk outputs require heightened governance. This taxonomy defines which outputs qualify, what evidence is required, and what Fast Path enforcement actions apply. The taxonomy is constitutional — it is not advisory.

Every high-risk output must have documented human review evidence. Every high-risk claim must be evaluated against the claim boundary. Every emission must be governed before it reaches its target.

---

*High-Risk Output Taxonomy v3.1 — EthicBit / CEMU v3.7.0+ — 2026-05-12*
