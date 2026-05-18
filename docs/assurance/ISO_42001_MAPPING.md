# ISO/IEC 42001:2023 — Mapping to EthicBit/CEMU Controls

**Version:** 1.0  
**Date:** 2026-05-18  
**Standard:** ISO/IEC 42001:2023 — Information technology — Artificial intelligence — Management system  
**Scope:** EthicBit/CEMU v4.0, AEM-EVOLVE v4.0  
**Status:** ACTIVE — informational mapping only; not a conformance assessment

---

## Clause 4 — Context of the Organization

| Clause | Requirement | EthicBit/CEMU Implementation | Status |
|--------|-------------|------------------------------|--------|
| 4.1 | Understanding the organization and its context | `docs/REPO_AUDIT_TRUTH_MODEL.md`; `docs/STATE_TAXONOMY_OFFICIAL.md`; canonical truth source at `artifacts/history/swarm/official_operational_status.json` | ADDRESSED |
| 4.2 | Understanding the needs of interested parties | External validators (criteria 1, 2, 8); anchor network operators; regulatory reviewers; outreach pack identifies stakeholder expectations | ADDRESSED |
| 4.3 | Determining the scope of the AI management system | Scope declared in `assurance/slsa/l4/level4-policy.json`; AEM-EVOLVE v4.0 declared scope in all assurance artifacts; `current_scope.artifacts` list | ADDRESSED |
| 4.4 | AI management system | Constitutional controls regime; sector-aware Mechanical Ethics (7 sectors: CORE, JUSTICIA, FINANZAS, SECURITY, TECHNICAL, LEGAL, REGULATORY); CEMU runtime | ADDRESSED |

---

## Clause 5 — Leadership

| Clause | Requirement | EthicBit/CEMU Implementation | Status |
|--------|-------------|------------------------------|--------|
| 5.1 | Leadership and commitment | Human review gate required for PRODUCTION_RELEASE class; `GATE_HUMAN_REVIEW` in `assurance/anchor/anchor-policy.json` | ADDRESSED |
| 5.2 | AI policy | `assurance/slsa/l4/level4-policy.json`; `assurance/anchor/anchor-policy.json`; `docs/LINGO_AND_CLAIM_DICTIONARY.md` defines claim scope policy | ADDRESSED |
| 5.3 | Organizational roles, responsibilities and authorities | Functionary identities embedded in in-toto statements (KMS signer ARN); `signedBy` field in all 6 statements; SLSA builder ID in provenance | ADDRESSED |

---

## Clause 6 — Planning

| Clause | Requirement | EthicBit/CEMU Implementation | Status |
|--------|-------------|------------------------------|--------|
| 6.1 | Actions to address risks and opportunities | STRIDE/LINDDUN/MITRE ATLAS threat model (`assurance/threat-model/threat-model.json`); 21 threats with mitigations and residual risk ratings | ADDRESSED |
| 6.1.2 | AI risk assessment process | Claim Boundary Engine (14-case red-team, 100% BLOCKED); Hypothesis property tests (I-1..I-M); Release-Grade Deep Audit (92/100) | ADDRESSED |
| 6.1.3 | AI risk treatment | FAIL_CLOSED posture; Block A-E remediation plan; no automated elevation to EXTERNAL_VALIDATION_PASS | ADDRESSED |
| 6.2 | AI management system objectives | Target: 7.5/10 external audit score post-remediation; 5/8 CONTROLLED_PASS; external validation of criteria 1, 2, 8 | ADDRESSED |

---

## Clause 7 — Support

| Clause | Requirement | EthicBit/CEMU Implementation | Status |
|--------|-------------|------------------------------|--------|
| 7.1 | Resources | AWS KMS keys (2 dedicated keys); GitHub Actions runners; CycloneDX SBOM toolchain (654 components); Python 3.11/3.12 + Node.js 20 | ADDRESSED |
| 7.2 | Competence | External validator process (HV-0..HV-10, 11 steps); independent reproduction support artifacts; validator invitation defines required competence | PARTIAL |
| 7.3 | Awareness | Public status bulletins in `docs/`; outreach pack; `docs/LINGO_AND_CLAIM_DICTIONARY.md` | ADDRESSED |
| 7.4 | Communication | `docs/external-validation/outreach/V4_0_EXTERNAL_REVIEWER_OUTREACH_PACK.md`; `V4_0_VALIDATOR_INVITATION.md`; public verification mirror | ADDRESSED |
| 7.5 | Documented information | `assurance/in-toto/attestation-index.json` (6 KMS-signed steps); `assurance/sbom/aem_v1_1_sbom.cyclonedx.sig.json`; `assurance/anchor/anchor-policy.json`; `assurance/slsa/subject-index.json` | ADDRESSED |

---

## Clause 8 — Operation

| Clause | Requirement | EthicBit/CEMU Implementation | Status |
|--------|-------------|------------------------------|--------|
| 8.1 | Operational planning and control | `assurance/anchor/anchor-policy.json` defines 4 release classes with prerequisites and gate scripts; `deployment/anchor_pre_deploy_gate.sh` | ADDRESSED |
| 8.2 | AI risk assessment (operational) | `assurance/threat-model/threat-model.json` operational scope; `tools/external_validation/claim_red_team/run_claim_red_team.py` run pre-release | ADDRESSED |
| 8.3 | AI risk treatment (operational) | FAIL_CLOSED enforced by CBE; KMS signing required before EXTERNAL_VALIDATION class anchor | ADDRESSED |
| 8.4 | AI system impact assessment | `docs/ai-me/HIGH_RISK_OUTPUT_TAXONOMY_V3_1.md` — high-risk output taxonomy by sector; sector gates in CI (CORE, JUSTICIA, FINANZAS, SECURITY, TECHNICAL, LEGAL, REGULATORY) | ADDRESSED |
| 8.5 | Documented AI system lifecycle | in-toto 6-step chain (intake → provenance → governance → fixation → sealing → closure) mirrors system lifecycle gates | ADDRESSED |
| 8.6 | Related organizational policies | `assurance/anchor/anchor-policy.json`; `assurance/slsa/l4/level4-policy.json`; `assurance/policies/` directory | ADDRESSED |

---

## Clause 9 — Performance Evaluation

| Clause | Requirement | EthicBit/CEMU Implementation | Status |
|--------|-------------|------------------------------|--------|
| 9.1 | Monitoring, measurement, analysis and evaluation | `health_check_weekly.yml`; `official-periodic-audit.yml`; `release-grade-discipline-gate.yml`; CBE block_rate monitored every CI run | ADDRESSED |
| 9.2 | Internal audit | `assurance/audit/RELEASE_GRADE_DEEP_AUDIT_REPORT_V1_0.json` (92/100); `AGGRESSIVE_VALIDATION_ABUSE_TEST_REPORT_V1_0.json` (100/100) | ADDRESSED |
| 9.3 | Management review | External audit 4/10 findings reviewed; 5-block remediation plan defined and executed (A+B+C complete, D+E in progress) | ADDRESSED |

---

## Clause 10 — Improvement

| Clause | Requirement | EthicBit/CEMU Implementation | Status |
|--------|-------------|------------------------------|--------|
| 10.1 | Nonconformity and corrective action | External audit finding C1 (SLSA contradiction) → Block A fix (`2063aca2`); finding C2 (unsigned in-toto) → Block B2 (`bf8822c7`); finding C3 (no active build workflow) → Block B3 (`23dd6f36`) | ADDRESSED |
| 10.2 | Continual improvement | SLSA trajectory: `SCHEMA_DEFINED_NOT_SIGNED` → `KMS_SIGNED_PENDING_EXTERNAL_WITNESS` → target external witness; audit score trajectory: 4/10 → 7.5/10 | ADDRESSED |

---

## Annex A — Controls (Selected)

| Control | Description | EthicBit/CEMU Implementation | Status |
|---------|-------------|------------------------------|--------|
| A.2.2 | AI risk assessment | STRIDE/LINDDUN/ATLAS (21 threats); Release-Grade Audit; property tests | ADDRESSED |
| A.3.3 | Data governance for AI | SBOM (654 components, CycloneDX 1.5, KMS-signed); `assurance/slsa/subject-index.json` (4 subjects, SHA256-bound) | ADDRESSED |
| A.4.2 | Intended use of AI system | Scope declarations in all artifacts; CBE blocks out-of-scope claims (financial, clinical, regulatory) | ADDRESSED |
| A.5.2 | Human oversight of AI system | Human review gate for PRODUCTION_RELEASE; HV-0..HV-10 external validation process; HUMAN_ATTESTATION_PENDING state enforced | ADDRESSED |
| A.6.1 | AI system documentation | `assurance/` directory structure; in-toto chain; SBOM; anchor receipts; outreach pack | ADDRESSED |
| A.8.2 | Testing and validation | Hybrid Validation Suite 11/11 COMPLETE; Hypothesis 8 tests; RuntimeGuard L4 negative tests; Fast Path 9/9 | ADDRESSED |
| A.9.3 | Transparency to affected parties | Public mirror (`EthicBit_CEMU_Public_Verification`); public anchor receipts; outreach pack | ADDRESSED |

---

## Conformance Gaps

| Gap | Clause | Impact | Path to Closure |
|-----|--------|--------|-----------------|
| Quantitative bias and fairness metrics not documented | A.8.2 | MEDIUM | Requires external security + fairness review (criterion 2) |
| Formal incident response runbook not yet written | 8.1 | LOW | Block E |
| Third-party conformance assessment not completed | 9.2 | HIGH | External validation criteria 1, 2, 8 |
| Privacy impact assessment not formalized | 4.2 | MEDIUM | LINDDUN partial; formal PIA not in scope for current release class |

---

*This document is an informational mapping, not an ISO/IEC 42001 conformance declaration. Formal conformance requires third-party certification body assessment.*
