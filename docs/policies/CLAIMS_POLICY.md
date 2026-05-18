# Claims Policy — EthicBit/CEMU

**Version:** 1.0 | **Date:** 2026-05-18  
**Authoritative dictionary:** `docs/LINGO_AND_CLAIM_DICTIONARY.md`  
**Enforcement:** `tools/external_validation/claim_red_team/` (CBE)

---

## 1. Purpose

This policy defines what claims EthicBit/CEMU may make publicly, what evidence is
required for each claim class, who can authorize a new claim, and what the structural
enforcement mechanism is.

---

## 2. Claim Classes

### Class 0 — STRUCTURAL_NON_CLAIM
Statements explicitly declared as **not claimed**. No evidence required.
Example: "EthicBit/CEMU does not claim regulatory approval."
Enforcement: CBE `non_claims` block; always `false`.

### Class 1 — CONTROLLED_EVIDENCE_CLAIM
Claim supported by controlled internal evidence. Human review not required.
Evidence requirements: automated test pass + artifact hash + anchor receipt.
Example: "Fast Path benchmark shows sub-15ms for scoped pre-execution path."
Approval: automated gate (CI + CBE).

### Class 2 — CONTROLLED_PASS_CLAIM
Claim supported by criterion-specific controlled evidence. 5/8 criteria currently at this level.
Evidence requirements: criterion artifact + controlled evidence report + anchor.
Example: "Criterion 4 (KMS/HSM) — CONTROLLED_PASS."
Approval: automated gate + release checklist.

### Class 3 — PENDING_EXTERNAL_CLAIM
Claim states that something is pending external validation. No false certainty.
Evidence requirements: support materials prepared + outreach initiated.
Example: "Criterion 1 (independent reproduction) — PENDING_EXTERNAL."
Approval: automated — only requires that outreach materials exist.

### Class 4 — EXTERNAL_VALIDATION_PASS_CLAIM
Claim that an external validator has independently validated a criterion.
Evidence requirements: signed validator attestation + specific criterion + scope declaration.
Approval: **cannot be set automatically**. Requires out-of-band human authorization and
`external_claim_review_completed = true` transition.

### Class 5 — PRODUCTION_RELEASE_CLAIM
Claim that the system is production-ready for a declared scope.
Evidence requirements: all Class 4 prerequisites + human attestation + in-toto external witness.
Approval: human review gate (GATE_HUMAN_REVIEW in anchor-policy.json).

---

## 3. Prohibited Automated Elevations

The following transitions **cannot occur through any automated process**:

| Prohibited transition | Why |
|-----------------------|-----|
| Any claim → `EXTERNAL_VALIDATION_PASS` | Requires human validator |
| `HUMAN_ATTESTATION_PENDING` → `HUMAN_ATTESTED` | Requires out-of-band sign-off |
| `CONTROLLED_PASS` → `CERTIFIED` | Certification requires third-party body |
| Any claim → `regulatory_approval` | Requires regulatory process |
| Any claim → `clinical_diagnostic` | Requires clinical validation process |

Enforced by: CBE (14 red-team cases), Hypothesis I-M meta-test, `check_claim_consistency.py`.

---

## 4. Scope Declaration Requirements

Every public claim **must** include a scope declaration that specifies:

- the artifact or system component it refers to
- the time window or version
- the test environment (if applicable)
- what is explicitly excluded from the claim

A claim without a scope declaration is treated as a Class 0 non-claim.

---

## 5. Adding a New Claim

To add a new public claim:

1. Add a case to `claim_boundary_regression_cases.json` that attempts the claim as an overclaim and verifies it is blocked.
2. If the claim has sufficient evidence, define it in `docs/LINGO_AND_CLAIM_DICTIONARY.md` with evidence requirements.
3. Run the full CBE suite: `python3 tools/external_validation/claim_red_team/run_claim_red_team.py --dry-run`
4. All existing cases must still block at 100%.
5. Merge via PR with `claim-boundary` and `property-tests` gates passing.

New Class 4 or Class 5 claims additionally require human review before merge.

---

## 6. Retiring a Claim

To retire an existing claim:

1. Update the relevant artifact status to reflect the change.
2. Add a non-claim entry if the retired claim could be confused with an active one.
3. Document the retirement reason in the PR description.
4. Do not remove the regression case from `claim_boundary_regression_cases.json` — update it to reflect the new scope.

---

## 7. Current Active Claims (as of 2026-05-18)

| Claim | Class | Evidence |
|-------|-------|----------|
| Fast Path sub-15ms (scoped pre-execution path only) | 1 | `assurance/fast-path/v1/` |
| AI-ME 12/12 PASS (v3.1) | 1 | `assurance/ai-me/v3_1/` |
| Criteria 3-7: CONTROLLED_PASS | 2 | `assurance/v4_0/evidence/` |
| Criteria 1, 2, 8: PENDING_EXTERNAL | 3 | Outreach pack prepared |
| SLSA BASELINE_DOCUMENTED | 1 | `assurance/slsa/l4/level4-policy.json` |
| in-toto chain KMS_SIGNED | 1 | `assurance/in-toto/attestation-index.json` |
| SBOM 654 components, KMS-signed | 1 | `assurance/sbom/aem_v1_1_sbom.cyclonedx.sig.json` |

---

*No Class 4 or Class 5 claims are currently active.*
