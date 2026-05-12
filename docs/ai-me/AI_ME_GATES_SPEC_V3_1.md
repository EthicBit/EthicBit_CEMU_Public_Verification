# AI-ME Gates Specification v3.1
## AI-Specific Mechanical Ethics Gate Suite

**Document type:** Technical Specification  
**Version:** 3.1  
**Status:** `SPECIFICATION_RELEASE`  
**Release type:** Specification Release (not Evidence Release)  
**Constitutional dependency:** EthicBit / CEMU v3.7.0+  
**Artifact assurance:** AEM v1.1  
**Date:** 2026-05-12

---

## Preamble

This document is a **Specification Release**, not an Evidence Release.

The gates defined here have not been fully implemented, executed, externally validated, certified, or approved for production use. This document defines what evidence is required, under what conditions, and to what acceptance criteria — so that future implementation can be measured against a constitutional standard.

---

## Overview

AEM-EVOLVE™ v3.1 defines the AI-Specific Mechanical Ethics Gate Suite: 12 gates required to operationalize Mechanical Ethics Assurance across model, data, agent, tool, memory, human-review and decision-governance domains.

| Gate | Name | Domain |
|---|---|---|
| AI-ME-01 | Model Evaluation Evidence | Model |
| AI-ME-02 | Bias / Fairness Evidence | Fairness |
| AI-ME-03 | Explainability Artifact Evidence | Explainability |
| AI-ME-04 | Data Provenance & Lineage Evidence | Data |
| AI-ME-05 | Agent Trace Capture Evidence | Agent |
| AI-ME-06 | Tool-Call Governance Evidence | Tool |
| AI-ME-07 | Memory Mutation Governance Evidence | Memory |
| AI-ME-08 | High-Risk Output Human Review Evidence | Human Oversight |
| AI-ME-09 | Multi-Agent Coordination Governance Evidence | Multi-Agent |
| AI-ME-10 | AI Red-Team / Adversarial Robustness Evidence | Security |
| AI-ME-11 | Decision Logging & Appealability Evidence | Decision |
| AI-ME-12 | AI Claim Boundary Enforcement Evidence | Claim |

---

## AI-ME-01 — Model Evaluation Evidence

**Gate ID:** AI-ME-01  
**Name:** Model Evaluation Evidence  
**Domain:** Model  

**Objective:** Verify that the AI model(s) used in the governed system have been evaluated against documented performance, capability and limitation criteria, and that evaluation artifacts exist and are verifiable.

**Constitutional Dependency:** EthicBit / CEMU v3.7.0+ — model claims are bound to model evaluation evidence.

**Inputs:**
- Model card or evaluation report
- Benchmark results (if applicable)
- Capability and limitation declarations
- Model version identifier

**Process / Checks:**
1. Verify model card exists and is hash-verifiable
2. Confirm evaluation methodology is documented
3. Confirm performance metrics are declared with scope
4. Confirm capability boundaries are declared
5. Confirm known limitations are declared

**Evidence Required:**
- Model evaluation artifact (model card, evaluation report, or equivalent)
- Hash record for the artifact
- Manifest entry in execution manifest

**Evidence Acceptance Criteria:**
- Artifact exists and hash matches AEM v1.1 manifest
- Evaluation scope is declared (not implied)
- Limitations are documented alongside capabilities
- Model version is explicitly identified

**AEM v1.1 Artifact Assurance Dependency:**  
Model evaluation artifact must be hash-verified through AEM v1.1 before AI-ME-01 can emit PASS.

**Fast Path Integration Potential:** Low — model evaluation evidence is not time-critical per enforcement tick.

**Outcomes:** PASS | SCOPE_LIMITED | FAIL_CLOSED | PENDING_EXTERNAL_REVIEW

**Claim Boundary:**  
Allowed: "Model evaluation evidence exists for [model] within [scope] as of [date]."  
Disallowed: "Our model is the best / safest / most capable."

**Recommended Integrations:** Model registry, evaluation framework output

**Non-claims:** This gate does not claim model superiority, external benchmarking, regulatory certification, or clinical/financial suitability.

---

## AI-ME-02 — Bias / Fairness Evidence

**Gate ID:** AI-ME-02  
**Name:** Bias / Fairness Evidence  
**Domain:** Fairness  

**Objective:** Verify that bias evaluation and fairness assessment artifacts exist for the governed model(s), within the declared evaluation scope and methodology.

**Constitutional Dependency:** EthicBit / CEMU v3.7.0+ — fairness claims are bound to fairness evidence.

**Inputs:**
- Fairness evaluation report or bias assessment artifact
- Evaluation methodology documentation
- Protected attribute scope declaration
- Dataset documentation

**Process / Checks:**
1. Verify fairness report exists and is hash-verifiable
2. Confirm evaluation methodology is documented
3. Confirm protected attributes evaluated are declared
4. Confirm evaluation dataset scope is declared
5. Confirm metrics and thresholds are documented

**Evidence Required:**
- Fairness evaluation artifact
- Hash record
- Methodology documentation reference

**Evidence Acceptance Criteria:**
- Artifact exists and hash matches AEM v1.1
- Evaluation scope is explicitly declared
- Protected attributes are named, not implied
- Methodology is documented and reproducible within scope

**AEM v1.1 Artifact Assurance Dependency:**  
Fairness artifact must be hash-verified through AEM v1.1. If artifact_verified = false, gate cannot emit PASS.

**Fast Path Integration Potential:** Low — fairness evidence does not require per-tick recalculation.

**Outcomes:** PASS | SCOPE_LIMITED | FAIL_CLOSED | PENDING_EXTERNAL_REVIEW

**Claim Boundary:**  
Allowed: "Fairness evaluation evidence exists for [scope] within [methodology] as of [date]."  
Disallowed: "Our AI is fully fair / unbiased / non-discriminatory."

**Recommended Integrations:** Fairness evaluation frameworks (Fairlearn, AI Fairness 360)

**Non-claims:** This gate does not claim universal fairness, legal non-discrimination compliance, or complete bias elimination.

---

## AI-ME-03 — Explainability Artifact Evidence

**Gate ID:** AI-ME-03  
**Name:** Explainability Artifact Evidence  
**Domain:** Explainability  

**Objective:** Verify that explainability artifacts exist for the governed model(s), demonstrating that model behavior can be interpreted within the declared scope and methodology.

**Constitutional Dependency:** EthicBit / CEMU v3.7.0+ — explainability claims are bound to explainability evidence.

**Inputs:**
- Explainability report or artifact (SHAP values, LIME outputs, attention maps, or equivalent)
- Methodology documentation
- Scope declaration

**Process / Checks:**
1. Verify explainability artifact exists and is hash-verifiable
2. Confirm methodology is documented
3. Confirm scope of explanations is declared
4. Confirm artifact format is specified

**Evidence Required:**
- Explainability artifact
- Hash record
- Methodology reference

**Evidence Acceptance Criteria:**
- Artifact exists and hash matches AEM v1.1
- Methodology is identified (not implied)
- Scope of application is declared
- Output format is documented

**AEM v1.1 Artifact Assurance Dependency:** Required. artifact_verified = false blocks PASS.

**Fast Path Integration Potential:** Low.

**Outcomes:** PASS | SCOPE_LIMITED | FAIL_CLOSED | PENDING_EXTERNAL_REVIEW

**Claim Boundary:**  
Allowed: "Explainability artifacts exist for [model] using [methodology] within [scope]."  
Disallowed: "Our AI is fully transparent and explainable."

**Non-claims:** This gate does not claim full model interpretability, regulatory explainability compliance, or universal applicability.

---

## AI-ME-04 — Data Provenance & Lineage Evidence

**Gate ID:** AI-ME-04  
**Name:** Data Provenance & Lineage Evidence  
**Domain:** Data  

**Objective:** Verify that data provenance and lineage artifacts exist for training and/or inference data used by the governed model(s).

**Constitutional Dependency:** EthicBit / CEMU v3.7.0+ — data claims are bound to data provenance evidence.

**Inputs:**
- Data lineage graph or provenance report
- Dataset documentation
- Data source declarations
- SBOM for data dependencies (if applicable)

**Process / Checks:**
1. Verify data lineage artifact exists and is hash-verifiable
2. Confirm data sources are documented
3. Confirm lineage graph covers declared scope
4. Confirm data transformation steps are recorded

**Evidence Required:**
- Data provenance artifact
- Hash record
- Source documentation

**Evidence Acceptance Criteria:**
- Artifact exists and hash matches AEM v1.1
- Data sources are named
- Lineage covers declared scope
- Transformation steps are documented

**AEM v1.1 Artifact Assurance Dependency:** Required. Critical gate for high-risk outputs.

**Fast Path Integration Potential:** Medium — data provenance snapshot can be inherited by Fast Path.

**Outcomes:** PASS | SCOPE_LIMITED | FAIL_CLOSED | PENDING_EXTERNAL_REVIEW

**Claim Boundary:**  
Allowed: "Data provenance evidence exists for [dataset] within [scope] as of [date]."  
Disallowed: "Our training data is fully clean, unbiased and legally compliant."

**Non-claims:** This gate does not claim legal data compliance, complete lineage coverage, or data quality certification.

---

## AI-ME-05 — Agent Trace Capture Evidence

**Gate ID:** AI-ME-05  
**Name:** Agent Trace Capture Evidence  
**Domain:** Agent  

**Objective:** Verify that agent execution traces are captured and preserved as evidence artifacts for governed agentic operations.

**Constitutional Dependency:** EthicBit / CEMU v3.7.0+ — agent behavior claims are bound to trace evidence.

**Important constraint:** AI-ME-05 does NOT capture raw chain-of-thought. It captures:
- **Rationale summary** — structured summary of agent reasoning
- **Planning metadata** — goal, sub-goals, plan selected
- **Decision trace** — key decision points and outcomes
- **Tool-call sequence** — ordered list of tool invocations
- **Memory mutation records** — what was read/written in memory
- **Execution metadata** — timestamps, agent ID, session ID

Raw chain-of-thought capture is prohibited. It may contain sensitive information, hallucinations, and partial reasoning that is not suitable as governance evidence.

**Evidence Required:**
- Agent trace artifact (rationale summary + planning metadata + decision trace + tool-call sequence)
- Memory mutation records
- Execution metadata

**Evidence Acceptance Criteria:**
- Trace artifact exists and hash matches AEM v1.1
- Rationale summary is structured (not raw LLM output)
- Tool-call sequence is complete for the governed operation
- Memory mutations are recorded

**AEM v1.1 Artifact Assurance Dependency:** Required.

**Fast Path Integration Potential:** Medium — trace metadata can feed Fast Path snapshot.

**Outcomes:** PASS | SCOPE_LIMITED | FAIL_CLOSED | NOT_APPLICABLE_WITH_JUSTIFICATION

**Claim Boundary:**  
Allowed: "Agent trace evidence exists for [operation] within [scope] as of [date]."  
Disallowed: "Our AI agent is fully transparent / auditable without qualification."

**Non-claims:** This gate does not claim complete agent interpretability, full chain-of-thought capture, or real-time tracing.

---

## AI-ME-06 — Tool-Call Governance Evidence

**Gate ID:** AI-ME-06  
**Name:** Tool-Call Governance Evidence  
**Domain:** Tool  

**Objective:** Verify that tool invocations by governed AI agents are authorized, logged, and preserved as governance evidence.

**Constitutional Dependency:** EthicBit / CEMU v3.7.0+ — tool invocation claims are bound to tool-call governance evidence.

**Inputs:**
- Tool-call logs
- Authorization policy for each tool
- Tool invocation records (tool name, parameters, response, timestamp, agent ID)

**Process / Checks:**
1. Verify tool-call log exists and is hash-verifiable
2. Confirm each logged tool call has an authorization reference
3. Confirm tool invocation parameters are logged (not just tool name)
4. Confirm tool response or error is logged
5. Confirm unauthorized tool call attempts are logged

**Evidence Required:**
- Tool-call governance log
- Authorization policy artifact
- Hash records

**Evidence Acceptance Criteria:**
- Log exists and hash matches AEM v1.1
- Authorization reference exists for each tool
- Invocation parameters are logged
- Unauthorized attempts are recorded

**AEM v1.1 Artifact Assurance Dependency:** Required. Critical gate — high Fast Path integration.

**Fast Path Integration Potential:** High — tool-call authorization can be enforced by Fast Path pre-emission.

**Outcomes:** PASS | SCOPE_LIMITED | FAIL_CLOSED

**Claim Boundary:**  
Allowed: "Tool-call governance evidence exists for [tools] within [scope]."  
Disallowed: "All tool calls are authorized and safe."

**Non-claims:** This gate does not claim universal tool authorization, external certification, or cybersecurity compliance.

---

## AI-ME-07 — Memory Mutation Governance Evidence

**Gate ID:** AI-ME-07  
**Name:** Memory Mutation Governance Evidence  
**Domain:** Memory  

**Objective:** Verify that memory mutations by governed AI agents are authorized, logged, and preserved as governance evidence.

**Constitutional Dependency:** EthicBit / CEMU v3.7.0+ — memory mutation claims are bound to mutation governance evidence.

**Inputs:**
- Memory mutation records
- Authorization policy for memory operations
- Pre/post state for material mutations (where feasible)

**Evidence Required:**
- Memory mutation governance log
- Authorization reference
- Hash record

**Evidence Acceptance Criteria:**
- Log exists and hash matches AEM v1.1
- Authorization reference exists for write/delete operations
- Material mutations include pre/post state reference

**AEM v1.1 Artifact Assurance Dependency:** Required.

**Fast Path Integration Potential:** Medium.

**Outcomes:** PASS | SCOPE_LIMITED | FAIL_CLOSED

**Non-claims:** This gate does not claim complete memory audit, tamper-proof storage, or immutable memory.

---

## AI-ME-08 — High-Risk Output Human Review Evidence

**Gate ID:** AI-ME-08  
**Name:** High-Risk Output Human Review Evidence  
**Domain:** Human Oversight  

**Objective:** Verify that high-risk outputs produced by governed AI systems have been reviewed by a human reviewer and that the review decision is preserved as a governance evidence artifact.

**Constitutional Dependency:** EthicBit / CEMU v3.7.0+ — human-in-the-loop claims are bound to HITL evidence.

**High-risk output categories (from High-Risk Taxonomy v3.1):**
- Financial decision support
- Cybersecurity response
- Regulatory / compliance decisions
- Clinical / medical support
- Public-sector decisions
- Identity / access / eligibility decisions
- Legal / quasi-legal decisions

**Inputs:**
- High-risk output identifier
- HITL decision record (reviewer ID, timestamp, decision, rationale)
- Output artifact

**Evidence Required:**
- HITL decision artifact
- Hash record
- Output artifact reference

**Evidence Acceptance Criteria:**
- HITL artifact exists and hash matches AEM v1.1
- Reviewer identity is recorded
- Decision (approve/reject/modify) is recorded
- Timestamp is recorded
- Output is bound to HITL decision

**AEM v1.1 Artifact Assurance Dependency:** Required. Critical gate — high Fast Path integration.

**Fast Path Integration Potential:** High — Fast Path can enforce HITL requirement before high-risk output emission.

**Outcomes:** PASS | SCOPE_LIMITED | FAIL_CLOSED

**Claim Boundary:**  
Allowed: "High-risk outputs within [category] have documented human review evidence as of [date]."  
Disallowed: "All AI outputs are human-reviewed."

**Non-claims:** This gate does not claim all outputs are high-risk, universal human oversight, or clinical/legal approval.

---

## AI-ME-09 — Multi-Agent Coordination Governance Evidence

**Gate ID:** AI-ME-09  
**Name:** Multi-Agent Coordination Governance Evidence  
**Domain:** Multi-Agent  

**Objective:** Verify that multi-agent coordination events are logged and governed, with evidence that agent roles, decisions, and handoffs are documented.

**Constitutional Dependency:** EthicBit / CEMU v3.7.0+.

**Evidence Required:**
- Multi-agent coordination log
- Agent role manifest
- Handoff records
- Hash records

**Evidence Acceptance Criteria:**
- Log exists and hash matches AEM v1.1
- Agent roles are declared
- Handoff events are logged
- Decision attribution is traceable to specific agent

**AEM v1.1 Artifact Assurance Dependency:** Required.

**Fast Path Integration Potential:** Low.

**Outcomes:** PASS | SCOPE_LIMITED | FAIL_CLOSED | NOT_APPLICABLE_WITH_JUSTIFICATION

**Non-claims:** This gate does not claim universal multi-agent governance, real-time coordination monitoring, or agent identity verification.

---

## AI-ME-10 — AI Red-Team / Adversarial Robustness Evidence

**Gate ID:** AI-ME-10  
**Name:** AI Red-Team / Adversarial Robustness Evidence  
**Domain:** Security  

**Objective:** Verify that adversarial robustness testing has been conducted on the governed AI system, with results preserved as evidence artifacts.

**Constitutional Dependency:** EthicBit / CEMU v3.7.0+.

**Evidence Required:**
- Red-team report or adversarial testing artifact
- Test methodology documentation
- Findings and mitigations record
- Hash records

**Evidence Acceptance Criteria:**
- Artifact exists and hash matches AEM v1.1
- Methodology is documented
- Findings are documented (not redacted without justification)
- Scope is declared

**AEM v1.1 Artifact Assurance Dependency:** Required.

**Fast Path Integration Potential:** Low.

**Outcomes:** PASS | SCOPE_LIMITED | FAIL_CLOSED | PENDING_EXTERNAL_REVIEW

**Non-claims:** This gate does not claim complete adversarial coverage, cybersecurity certification, or external security approval.

---

## AI-ME-11 — Decision Logging & Appealability Evidence

**Gate ID:** AI-ME-11  
**Name:** Decision Logging & Appealability Evidence  
**Domain:** Decision  

**Objective:** Verify that AI-influenced decisions are logged with sufficient detail to support review and appeal processes, and that appeal procedures exist and are documented.

**Constitutional Dependency:** EthicBit / CEMU v3.7.0+.

**Evidence Required:**
- Decision log artifact
- Appeal procedure documentation
- Hash records

**Evidence Acceptance Criteria:**
- Decision log exists and hash matches AEM v1.1
- Log entries include: decision ID, timestamp, model/agent ID, input summary, output summary, confidence (if applicable), human review status
- Appeal procedure is documented and accessible

**AEM v1.1 Artifact Assurance Dependency:** Required.

**Fast Path Integration Potential:** Low.

**Outcomes:** PASS | SCOPE_LIMITED | FAIL_CLOSED

**Non-claims:** This gate does not claim legal appealability, regulatory compliance, or judicial review readiness.

---

## AI-ME-12 — AI Claim Boundary Enforcement Evidence

**Gate ID:** AI-ME-12  
**Name:** AI Claim Boundary Enforcement Evidence  
**Domain:** Claim  

**Objective:** Verify that the Claim Boundary Engine™ has produced and preserved enforcement logs demonstrating that AI governance claims were evaluated against verified evidence before emission.

**Constitutional Dependency:** EthicBit / CEMU v3.7.0+ — claim boundary enforcement is constitutionally mandated.

**Inputs:**
- Claim boundary enforcement logs
- Claim-level ceiling records
- Fast Path enforcement verdicts (where applicable)

**Evidence Required:**
- Claim boundary enforcement log
- Hash record
- Fast Path verdict records (where Fast Path is active)

**Evidence Acceptance Criteria:**
- Enforcement log exists and hash matches AEM v1.1
- Each evaluated claim has a recorded outcome (PASS / SCOPE_LIMITED / FAIL_CLOSED)
- Claim-level ceiling is recorded per claim evaluation
- Fast Path verdicts are bound to enforcement log entries (where applicable)

**AEM v1.1 Artifact Assurance Dependency:** Required. Critical gate — high Fast Path integration.

**Fast Path Integration Potential:** High — AI-ME-12 enforcement logs are core Fast Path inputs.

**Outcomes:** PASS | SCOPE_LIMITED | FAIL_CLOSED

**Claim Boundary:**  
Allowed: "Claim boundary enforcement evidence exists for [claims evaluated] within [scope]."  
Disallowed: "All AI claims are validated and compliant."

**Non-claims:** This gate does not claim universal claim coverage, regulatory compliance, or legal certification.

---

## Fast Path Integration Summary

| Gate | Fast Path Candidate | Fast Path Scope |
|---|---|---|
| AI-ME-01 | Low | — |
| AI-ME-02 | Low | — |
| AI-ME-03 | Low | — |
| AI-ME-04 | Medium | Data provenance snapshot inheritance |
| AI-ME-05 | Medium | Trace metadata snapshot |
| AI-ME-06 | **High** | Tool-call authorization pre-emission |
| AI-ME-07 | Medium | Memory mutation authorization |
| AI-ME-08 | **High** | HITL requirement enforcement before high-risk emission |
| AI-ME-09 | Low | — |
| AI-ME-10 | Low | — |
| AI-ME-11 | Low | — |
| AI-ME-12 | **High** | Claim boundary enforcement enforcement log |

---

## Claim

AEM-EVOLVE™ v3.1 defines the AI-Specific Mechanical Ethics Gate Suite required to operationalize Mechanical Ethics Assurance across model, data, agent, tool, memory, human-review and decision-governance domains.

## Non-Claims

This specification does not claim that AI-ME Gates have been fully implemented, executed, externally validated, certified or approved for production use.

---

*AI-ME Gates Specification v3.1 — EthicBit / CEMU v3.7.0+ — 2026-05-12*
