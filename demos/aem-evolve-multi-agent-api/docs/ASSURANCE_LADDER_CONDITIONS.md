# AEM-EVOLVE Multi-Agent Governance API — Assurance Ladder Trigger Conditions

**Version:** 0.3.1-demo  
**Current milestone:** PR 7 — Production-Readiness Hardening (merged)  
**Status:** PRs 1–7 complete. PRs 8+ are conditional — no work begins until the trigger conditions below are formally satisfied and recorded.

---

## How to use this document

Each conditional PR has a **trigger gate**: a set of conditions that must be met before that PR may be opened. When all conditions for a PR are satisfied, the responsible party records the evidence in `assurance/evolve-multi-agent/` (a new artifact per gate) and opens the PR referencing that evidence. Work on a later PR cannot begin until all prior gates are satisfied.

---

## PR 8 — External Review / Certification

### Trigger conditions (ALL required)

| # | Condition | Evidence required |
|---|---|---|
| 8.1 | A named external reviewer or certification body has formally accepted engagement | Signed engagement letter or written acceptance (email or document); reviewer name and organization recorded |
| 8.2 | Scope of review is defined in writing | Review scope document listing: artifact version, claims under review, claims explicitly out of scope, and applicable standard or framework (e.g. ISO 42001, SOC 2, internal audit framework) |
| 8.3 | Independent reproduction has been executed by a party other than EthicBit | Written reproduction report from the third party confirming `AEM_EVOLVE_REPRODUCTION_CHALLENGE_STATUS=ALL_MATCH` and behavioral outcomes from `run_demo_e2e.sh` |
| 8.4 | A defined deployment environment exists | Environment specification document: OS, Python version, database backend, network topology, secrets management approach |

### What PR 8 unlocks

The claim: *"AEM-EVOLVE Multi-Agent Governance API v0.3.1 has been externally reviewed for [defined scope] by [named reviewer]."*

### What PR 8 does NOT unlock

- Regulatory approval of any kind.
- Clinical or diagnostic use.
- Certification outside the defined review scope.
- HSM-backed key custody (unless separately evidenced).

### Gate artifact to create

`assurance/evolve-multi-agent/AEM_EVOLVE_PR8_GATE_RECORD.json`  
Fields: `reviewer_name`, `reviewer_organization`, `engagement_confirmed_date`, `review_scope_path`, `reproduction_report_path`, `environment_spec_path`, `conditions_satisfied`.

---

## PR 9 — Regulatory Pathway

### Trigger conditions (ALL required)

| # | Condition | Evidence required |
|---|---|---|
| 9.1 | A specific intended use has been defined and documented | Intended Use Statement: describes the user population, use context, decision supported, and what the system does NOT do |
| 9.2 | A jurisdiction and applicable regulatory framework have been selected | Written selection: e.g. EU AI Act (Article 6 risk classification), FDA SaMD guidance, MDR/IVDR, or equivalent; with rationale for applicability |
| 9.3 | A regulatory counsel or qualified person (QP) has been engaged | Engagement confirmation from qualified regulatory counsel or notified body |
| 9.4 | A gap analysis against the selected framework has been completed | Gap analysis document listing: requirements met, requirements partially met, requirements not yet met, and remediation plan |
| 9.5 | PR 8 gate is satisfied | `AEM_EVOLVE_PR8_GATE_RECORD.json` exists with `conditions_satisfied: true` |

### What PR 9 unlocks

The claim: *"AEM-EVOLVE is under regulatory assessment for [intended use] under [framework] in [jurisdiction]."*

### What PR 9 does NOT unlock

- Regulatory approval (that requires completed assessment and authority decision).
- Clinical or diagnostic use.
- Marketing or deployment claims.

### Gate artifact to create

`assurance/evolve-multi-agent/AEM_EVOLVE_PR9_GATE_RECORD.json`  
Fields: `intended_use_statement_path`, `jurisdiction`, `regulatory_framework`, `regulatory_counsel_name`, `gap_analysis_path`, `pr8_gate_satisfied`, `conditions_satisfied`.

---

## PR 10 — Clinical / Diagnostic Pathway

### Trigger conditions (ALL required)

| # | Condition | Evidence required |
|---|---|---|
| 10.1 | A named clinical or medical stakeholder (institution, PI, or CMO) has formally confirmed the intended clinical use case | Written confirmation from clinical stakeholder: institution, role, proposed use, patient population |
| 10.2 | A clinical risk classification has been completed | Risk classification document per applicable framework (e.g. ISO 14971, IEC 62304, FDA SaMD risk framework); class level recorded with rationale |
| 10.3 | A data governance and patient privacy analysis has been completed | Analysis document addressing: data types involved, applicable privacy regulation (HIPAA, GDPR, etc.), de-identification approach, and consent framework |
| 10.4 | A clinical validation protocol has been defined | Protocol document: study design, endpoints, sample size rationale, success criteria, IRB/ethics board path |
| 10.5 | PR 9 gate is satisfied | `AEM_EVOLVE_PR9_GATE_RECORD.json` exists with `conditions_satisfied: true` |

### What PR 10 unlocks

The claim: *"AEM-EVOLVE is under clinical assessment for [defined clinical use] under [risk class] with [named institution]."*

### What PR 10 does NOT unlock

- Clinical validation (that requires completed study and peer review).
- Diagnostic approval.
- Any claim of clinical efficacy or safety.

### Gate artifact to create

`assurance/evolve-multi-agent/AEM_EVOLVE_PR10_GATE_RECORD.json`  
Fields: `clinical_stakeholder_name`, `clinical_institution`, `proposed_clinical_use`, `risk_classification_path`, `risk_class_level`, `data_governance_path`, `clinical_validation_protocol_path`, `pr9_gate_satisfied`, `conditions_satisfied`.

---

## Gate dependency chain

```
PR 7 (merged)
    └── PR 8 gate: 8.1 + 8.2 + 8.3 + 8.4 satisfied
            └── PR 9 gate: 9.1 + 9.2 + 9.3 + 9.4 + PR8 satisfied
                    └── PR 10 gate: 10.1 + 10.2 + 10.3 + 10.4 + PR9 satisfied
```

A PR may not be opened until its gate record exists and `conditions_satisfied: true`.

---

## Non-claims (permanent until gate is satisfied)

| Non-claim | Lifted by |
|---|---|
| `externally_certified: false` | PR 8 gate satisfied + PR 8 merged |
| `regulatory_approved: false` | Completed regulatory assessment (beyond PR 9 scope) |
| `clinical_or_diagnostic: false` | Completed clinical validation (beyond PR 10 scope) |
| `independently_reproduced: false` | Condition 8.3 satisfied |
| `hsm_backed: false` | Separate HSM integration PR (not on current ladder) |

---

## Current gate status

| Gate | Status |
|---|---|
| PR 8 gate | **NOT SATISFIED** — no external reviewer engaged, no independent reproduction report |
| PR 9 gate | **NOT SATISFIED** — depends on PR 8 gate |
| PR 10 gate | **NOT SATISFIED** — depends on PR 9 gate |
