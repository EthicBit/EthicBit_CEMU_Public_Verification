# Criterion 8 — External Claim Review Package

**Criterion:** Independent external claim boundary review  
**Status:** `PENDING_EXTERNAL` — awaiting external reviewer  
**Package version:** 2.0 | **Date:** 2026-05-18  
**HEAD commit:** `66fbce1d`

---

## What the reviewer must do

1. Review the 14 claim boundary regression cases and verify all should be blocked.
2. Review the claims policy and non-claims inventory.
3. Evaluate whether scope declarations on active claims are accurate and sufficient.
4. Identify any overclaims not currently covered by the CBE.
5. Issue a scoped attestation: `CLAIM_REVIEW_PASS / CLAIM_REVIEW_PARTIAL / CLAIM_REVIEW_FAIL`.

---

## Primary artifacts for review

### Claim Boundary Engine (CBE)
`tools/external_validation/claim_red_team/claim_boundary_regression_cases.json`  
14 cases (CBRT-001..CBRT-014) covering: regulatory approval, production readiness, cybersecurity certification, financial advice, clinical diagnostics, tamper-proof, universal anchor, sub-15ms full system, third-party reproduction, external certification, SLSA L4 fully achieved, SLSA L4 certified, production supply chain certified, externally verified in-toto chain.

Reviewer should: confirm each blocked claim is correctly classified as unsupported given current evidence; identify any claims that should be on this list but are not.

### Claims policy
`docs/policies/CLAIMS_POLICY.md`  
5 claim classes (STRUCTURAL_NON_CLAIM through PRODUCTION_RELEASE_CLAIM). Prohibited automated elevations. Process for adding/retiring claims. Active claims inventory.

Reviewer should: evaluate whether the class definitions are sound; check whether any active claims exceed their evidence base.

### Active claims to evaluate

| Claim | Class | Evidence base | Location |
|-------|-------|---------------|----------|
| Fast Path sub-15ms (scoped pre-execution path only) | 1 | Fast Path report 9/9 | `assurance/fast-path/v1/` |
| AI-ME 12/12 PASS (v3.1) | 1 | AI-ME aggregate report | `assurance/ai-me/v3_1/` |
| Criteria 3-7: CONTROLLED_PASS | 2 | Criterion artifacts | `assurance/v4_0/evidence/` |
| Criteria 1, 2, 8: PENDING_EXTERNAL | 3 | Outreach initiated | This package |
| SLSA BASELINE_DOCUMENTED | 1 | level4-policy.json | `assurance/slsa/l4/` |
| in-toto chain KMS_SIGNED (6/6) | 1 | attestation-index.json | `assurance/in-toto/` |
| SBOM 654 components, KMS-signed | 1 | SBOM sidecar | `assurance/sbom/` |

### Non-claims inventory (verify all false)
`tools/external_validation/claim_red_team/claim_boundary_regression_cases.json` — `non_claims` section  
`docs/policies/CLAIMS_POLICY.md` — Class 0 section  
`assurance/anchor/anchor-policy.json` — `non_claims` block  
`assurance/threat-model/threat-model.json` — `summary.non_claims`  

Reviewer should: independently verify that none of the 13 non-claim fields are asserted as true anywhere in the public-facing artifacts.

### Framework comparative analysis
`docs/assurance/FRAMEWORK_COMPARATIVE_ANALYSIS.md`  
Positions EthicBit/CEMU against SLSA, in-toto, SSDF. Reviewer should: verify the positioning table is accurate; flag any overclaims in the comparative positioning.

### Hypothesis property tests
`tests/test_claim_boundary_properties.py`  
Test I-5: verifies all 13 non-claims are false. Test I-M: verifies that injecting a non-BLOCKED case fails the report.  
Reviewer should: run `pytest tests/test_claim_boundary_properties.py -v` and confirm 8/8 pass.

---

## What constitutes a CLAIM_REVIEW_PASS

- All 14 CBE cases reviewed; reviewer agrees they should be blocked.
- No unregistered overclaim found in public-facing materials.
- Active claims reviewed; all assessed as within evidence base with scope declarations.
- Non-claims verified: no false positive assertions found.
- Hypothesis tests confirmed passing in reviewer's environment.

## Non-claims

- Claim review does **not** constitute regulatory approval.
- A CLAIM_REVIEW_PASS applies to the reviewed scope and snapshot only.
- Claim review does **not** elevate any criterion to EXTERNAL_VALIDATION_PASS automatically — that requires reviewer's signed attestation.

---

## Attestation template

```
CRITERION_8_EXTERNAL_CLAIM_REVIEW_ATTESTATION
Reviewer: [name / org / affiliation]
Date: [ISO date]
Commit reviewed: [git SHA]
CBE cases reviewed: [14/14 or subset]
Unregistered overclaims found: [yes/no — list if yes]
Active claims within evidence base: [yes / concerns noted]
Non-claims verified: [yes / discrepancies noted]
Hypothesis tests: [8/8 pass / not run]
Result: [CLAIM_REVIEW_PASS / CLAIM_REVIEW_PARTIAL / CLAIM_REVIEW_FAIL]
Scope: [explicit limitations]
Signature: [PGP / GitHub commit / other]
```

---

## New since 2026-05-14 (relevant to this criterion)

- `docs/policies/CLAIMS_POLICY.md` — formal claims policy with 5 classes (Block E, new)
- CBE now covers 14 cases (CBRT-011..014 added: SLSA L4, supply-chain, in-toto)
- `tests/test_claim_boundary_properties.py` — Hypothesis I-M: meta-invariant test (Block C, new)
- `docs/assurance/FRAMEWORK_COMPARATIVE_ANALYSIS.md` — claim positioning vs SLSA/in-toto/SSDF (Block D, new)
- `docs/assurance/NIST_AI_RMF_MAPPING.md` — MANAGE section covers claim boundary (Block D, new)
- `assurance/anchor/anchor-policy.json` — anchor-level non-claims section (Block B5, new)
