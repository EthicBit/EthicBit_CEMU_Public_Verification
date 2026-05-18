# NIST AI RMF 1.0 — Mapping to EthicBit/CEMU Controls

**Version:** 1.0  
**Date:** 2026-05-18  
**Framework:** NIST AI Risk Management Framework 1.0 (January 2023)  
**Scope:** EthicBit/CEMU v4.0, AEM-EVOLVE v4.0  
**Status:** ACTIVE — coverage is partial; gaps noted inline

---

## GOVERN

Policies, accountability structures, and oversight mechanisms for AI risk management.

| Sub-function | NIST RMF Guidance | EthicBit/CEMU Control | Status |
|---|---|---|---|
| GV-1.1 | Org context and risk tolerance documented | Constitutional controls regime, sector-aware Mechanical Ethics; `docs/STATE_TAXONOMY_OFFICIAL.md`; `docs/REPO_AUDIT_TRUTH_MODEL.md` | IMPLEMENTED |
| GV-1.2 | AI risk policies established | `assurance/anchor/anchor-policy.json` (release class gates); `assurance/slsa/l4/level4-policy.json` (FAIL_CLOSED enforcement) | IMPLEMENTED |
| GV-1.3 | Accountability for AI risks assigned | KMS signer ARN embedded in every signed artifact; CEERV `case_003` FORMALLY_FROZEN with functionary identity | IMPLEMENTED |
| GV-2.1 | Oversight mechanisms in place | Human review gate required for PRODUCTION_RELEASE anchor; `GATE_HUMAN_REVIEW` in anchor-policy.json | IMPLEMENTED |
| GV-2.2 | Third-party risk oversight | External validation outreach pack + validator invitation for criteria 1, 2, 8; PENDING_EXTERNAL | PARTIAL |
| GV-3.1 | Team competence and diversity | External validator process (HV-0..HV-10, 11 steps); independent reproduction support artifacts | PARTIAL |
| GV-4.1 | Org risk tolerance communicated | SLSA `full_l4_claim_allowed: false`; `human_attestation_status: HUMAN_ATTESTATION_PENDING`; CBE non-claims section | IMPLEMENTED |
| GV-5.1 | Policies aligned to applicable laws | `docs/ETHICBIT_REGULATORY_BRIEF.md`; ISO 42001 mapping (see companion document) | PARTIAL |
| GV-5.2 | Privacy considerations documented | LINDDUN threat model (LIN-001..LIN-005); `.gitignore` excludes PII-bearing files | PARTIAL |
| GV-6.1 | Incident response plans | Block A-E remediation plan (structured response to external audit 4/10 finding) | PARTIAL — no formal incident runbook yet (Block E) |

---

## MAP

Context establishment, risk identification, and impact categorization.

| Sub-function | NIST RMF Guidance | EthicBit/CEMU Control | Status |
|---|---|---|---|
| MP-1.1 | Intended use and context documented | AEM-EVOLVE v4.0 scope declared in every artifact; criterion-by-criterion scope in outreach pack | IMPLEMENTED |
| MP-1.5 | Organizational risk tolerance bounded | `level4-policy.json` risk_modes: STANDARD / HIGH / GOV with escalating signature requirements | IMPLEMENTED |
| MP-2.1 | Scientific and technical limitations acknowledged | `PASS_WITH_SCOPE_LIMITATIONS` on both audits; 3/8 PENDING_EXTERNAL; `full_l4_claim_allowed: false` | IMPLEMENTED |
| MP-2.3 | AI system impact categorized | `docs/ai-me/HIGH_RISK_OUTPUT_TAXONOMY_V3_1.md` — high-risk output categories defined per sector | IMPLEMENTED |
| MP-3.1 | AI risks identified | STRIDE/LINDDUN/MITRE ATLAS threat model (`assurance/threat-model/threat-model.json`) — 21 threats | IMPLEMENTED |
| MP-3.4 | Negative impacts on individuals identified | CBE blocks: financial_advice_claim, clinical_diagnostic_claim; LINDDUN LIN-004 non-compliance threat | IMPLEMENTED |
| MP-4.1 | Risk classified by severity | Threat model risk_rating HIGH/MEDIUM/LOW; 9 HIGH, 10 MEDIUM, 2 LOW | IMPLEMENTED |
| MP-4.2 | Risk to vulnerable populations noted | Sector-aware ME gates (JUSTICIA, FINANZAS, LEGAL, REGULATORY); CBE blocks clinical and financial overclaims | IMPLEMENTED |
| MP-5.1 | Likelihood and impact of AI risks estimated | Release-Grade Deep Audit v1.0 score 92/100; external audit 4/10 with specific gap analysis | IMPLEMENTED |

---

## MEASURE

Risk analysis, testing, evaluation, and monitoring.

| Sub-function | NIST RMF Guidance | EthicBit/CEMU Control | Status |
|---|---|---|---|
| MS-1.1 | Risk measurement approach defined | Block rate (CBE), audit scores (92/100, 100/100), SLSA level target, in-toto signing status | IMPLEMENTED |
| MS-2.1 | AI system tested for intended use | Hybrid Validation Suite HV-0..HV-10 (11/11 COMPLETE); Fast Path benchmark (9/9 EVIDENCE_PASS) | IMPLEMENTED |
| MS-2.2 | Adversarial testing performed | Hypothesis property tests (8 tests, 500 examples); 14 red-team claim boundary cases; RuntimeGuard L4 negative tests | IMPLEMENTED |
| MS-2.5 | Explainability/interpretability assessed | CEERV evidence bundle documents decision trace for case_003; structured JSON outputs with rationale fields | PARTIAL |
| MS-2.6 | Bias and fairness evaluated | Sector-aware ME gates enforce sector-specific rules; no quantitative fairness metrics documented | GAP |
| MS-2.7 | Robustness tested | FAIL_CLOSED posture on all constitutional gates; RuntimeGuard L4 operative baseline | IMPLEMENTED |
| MS-3.1 | Monitoring mechanisms in place | `health_check_weekly.yml`; `official-periodic-audit.yml`; triple anchor reverification | IMPLEMENTED |
| MS-3.2 | Feedback incorporated | Block A-E remediation from external audit; audit findings addressed in 6 commits | IMPLEMENTED |
| MS-4.1 | Traceability of AI outputs | in-toto 6-step chain (intake→closure), all KMS-signed; CEERV FORMALLY_FROZEN; anchor receipts | IMPLEMENTED |
| MS-4.2 | Audit trail maintained | Triple Public Anchor (Sepolia + Arweave + AO); Mainnet KZG blob; git history with signed commits | IMPLEMENTED |

---

## MANAGE

Risk treatment, response planning, recovery, and communication.

| Sub-function | NIST RMF Guidance | EthicBit/CEMU Control | Status |
|---|---|---|---|
| MG-1.1 | Risk response plans implemented | FAIL_CLOSED default on all CBE and constitutional gates; no automated elevation to EXTERNAL_VALIDATION_PASS | IMPLEMENTED |
| MG-1.3 | Risk prioritized by impact | External audit 4/10 → 5-block remediation plan (A→E) with explicit sequence and target score 7.5/10 | IMPLEMENTED |
| MG-2.2 | Residual risks documented | Threat model `summary.primary_residual_gaps`; scope limitations in both audit reports | IMPLEMENTED |
| MG-2.4 | Risk treatment verified | Hypothesis tests (I-M meta-invariant); CI gates on every push; Block A resolves SLSA contradiction | IMPLEMENTED |
| MG-3.1 | Incident response plans | Block A-E remediation structure; CEERV FORMALLY_FROZEN as recovery-complete marker for case_003 | PARTIAL — no formal runbook (Block E) |
| MG-3.2 | Rollback and recovery | Git history provides rollback; CEERV PASS_REFERENCE_ONLY preserves recovery baseline | IMPLEMENTED |
| MG-4.1 | Communication to affected parties | External validator outreach pack; validator invitation; public status bulletins in `docs/` | IMPLEMENTED |
| MG-4.2 | Findings disclosed | Release-Grade Deep Audit and Aggressive Validation published in `assurance/audit/`; external audit 4/10 incorporated | IMPLEMENTED |

---

## Gap Summary

| Gap | Sub-function | Severity | Planned Mitigation |
|-----|-------------|----------|--------------------|
| Quantitative bias/fairness metrics | MS-2.6 | MEDIUM | Block D coverage; external security review criterion 2 |
| Formal incident runbook | GV-6.1, MG-3.1 | LOW | Block E |
| Full third-party risk review | GV-2.2 | HIGH | External validation criteria 1, 2, 8 (pending) |
| ISO/IEC 27001 or equivalent certification | GV-5.1 | MEDIUM | Out of scope for current release class |

---

*This mapping is scoped to EthicBit/CEMU v4.0 and reflects controls implemented as of 2026-05-18. It does not constitute NIST AI RMF certification or conformance assessment.*
