# AEM-EVOLVE v4.0 Human Attestation Protocol

**System:** EthicBit / CEMU  
**Layer:** AEM-EVOLVE v4.0 hybrid validation support  
**Document type:** Human attestation protocol  
**Status:** `HUMAN_ATTESTATION_PROTOCOL_DEFINED`  
**Depends on:** `V4_0_HYBRID_VALIDATION_SUPPORT_MODEL.md`, `V4_0_NOTARY_DOSSIER_STRUCTURE.md`

---

## 1. Purpose

This document defines the human attestation protocol for scoped external review of the AEM-EVOLVE v4.0 Notary Dossier.

The protocol prevents automated evidence from being treated as external validation unless a human reviewer evaluates the dossier, declares scope, reviews methodology and limitations, and signs a scoped attestation.

The reviewer does not certify the entire EthicBit system. The reviewer attests only the declared review scope.

---

## 2. Protocol Summary

The human attestation protocol follows this flow:

```text
Notary Dossier prepared
  -> reviewer receives dossier and hash record
  -> reviewer declares scope
  -> reviewer reviews integrity and methodology
  -> reviewer reviews claim boundaries and limitations
  -> reviewer records PASS / PARTIAL / FAIL / OUT_OF_SCOPE
  -> reviewer signs scoped attestation
  -> claim-state governance evaluates permissible claim elevation
```

No claim elevation may occur without scoped human attestation.

---

## 3. Required Validation Order

The attestation protocol follows a substance-first order:

```text
independent technical reproduction
  -> threat model and external red-team / security review
  -> scoped human attestation
```

This order prevents human attestation from becoming a cosmetic seal over internally generated evidence.

An attestation may be accepted as `PARTIAL` or `OUT_OF_SCOPE` if it reviews only a subset of the dossier. It must not elevate the system to `EXTERNAL_VALIDATION_PASS` unless independent reproduction, threat-model/security review, claim-boundary review, scope declaration, limitations, and signature requirements are all satisfied within the declared scope.

---

## 4. Reviewer Role

The reviewer evaluates:

- dossier integrity;
- selected hash recomputation;
- evidence methodology;
- reproduction-support evidence;
- security-review support evidence;
- claim-boundary red-team evidence;
- public mirror sanitization posture;
- scope limitations;
- non-claims;
- whether the requested claim is supported by the declared evidence.

The reviewer does not provide automatic regulatory approval, cybersecurity certification, legal advice, clinical validation, financial advice, or universal production-readiness approval.

---

## 5. Required Reviewer Declarations

A valid attestation must include:

- reviewer name or organization;
- reviewer role or qualification summary;
- review date UTC;
- repository reference reviewed;
- dossier manifest reviewed;
- dossier hash or hash record reviewed;
- declared scope;
- domains reviewed;
- methodology notes;
- independent reproduction review status;
- threat-model or external red-team/security review status;
- limitations;
- final scoped outcome;
- signature or equivalent approval evidence.

---

## 6. Attestation Outcomes

Allowed human attestation outcomes:

```text
PASS
PARTIAL
FAIL
OUT_OF_SCOPE
```

Recommended meaning:

| Outcome | Meaning |
|---|---|
| `PASS` | Evidence is sufficient for the declared scope reviewed. |
| `PARTIAL` | Evidence is partially sufficient, with limitations or exclusions. |
| `FAIL` | Evidence is insufficient or materially inconsistent. |
| `OUT_OF_SCOPE` | Reviewer did not evaluate the requested claim or domain. |

A `PASS` does not imply certification outside the declared scope.

---

## 7. Scope Requirements

Every attestation must state what was reviewed and what was not reviewed.

Minimum scope fields:

```text
reviewed_repository_reference
reviewed_commit_or_tag
reviewed_dossier_hash
reviewed_criteria
reviewed_artifacts
reviewed_methods
excluded_artifacts
excluded_claims
limitations
```

If scope is missing, the attestation must be treated as invalid for external-validation elevation.

---

## 8. Claim-State Interaction

A human attestation may support state transition only if:

```text
reviewer_scope_declared=true
independent_reproduction_reviewed=true
threat_model_review_completed=true
external_red_team_or_security_review_completed=true
methodology_review_completed=true
dossier_hashes_verified=true
claim_boundary_review_completed=true
limitations_declared=true
no_forbidden_claims=true
signed_human_attestation=true
```

If any condition is missing, claim-state governance must remain at:

```text
HUMAN_ATTESTATION_PENDING
```

or move to:

```text
FAIL_CLOSED
```

as appropriate.

---

## 9. Required Attestation Statement

The reviewer may use this safe statement:

```text
I reviewed the provided AEM-EVOLVE v4.0 Notary Dossier for the scoped criteria listed in this attestation. I found the evidence package [PASS / PARTIAL / FAIL / OUT_OF_SCOPE] for integrity, methodology, scope and claim-boundary review within the declared scope. This attestation does not constitute regulatory approval, external certification, cybersecurity certification, financial advice, clinical validation, diagnostic authorization, legal advice or universal production-readiness approval.
```

---

## 10. Forbidden Attestation Claims

The attestation must not claim, unless separately evidenced and explicitly in scope:

- regulatory approval;
- FDA, EMA or equivalent approval;
- cybersecurity certification;
- external certification of the full system;
- legal compliance;
- financial advice;
- clinical validation;
- diagnostic authorization;
- absence of all vulnerabilities;
- universal production readiness;
- universal public anchoring;
- tamper-proof storage;
- third-party reproduction if reproduction was not independently executed;
- external security review if security methodology was not reviewed.
- SLSA L4 fully achieved while in-toto remains unverified;
- SLSA L4 certified without named certification evidence;
- production supply-chain certified without named production certification evidence;
- externally verified in-toto chain without signed external verification.

---

## 11. Evidence Review Checklist

The reviewer should inspect:

- `DOSSIER_MANIFEST.json`;
- `DOSSIER_HASH_RECORD.txt`, if present;
- automated reproduction support report, if present;
- automated security review support summary, if present;
- claim-boundary red-team report, if present;
- cloud and KMS evidence summaries, if present;
- anchor reference summary, if present;
- methodology review notes;
- non-claims;
- public mirror sanitization notes.

If a listed artifact is absent, the reviewer should record it as missing, out of scope, or not yet generated.

---

## 12. Public Mirror Handling

A signed attestation may be published to the public verification mirror only after sanitization review.

Public attestation should not disclose:

- private keys;
- secrets;
- database credentials;
- private infrastructure configuration;
- account IDs;
- unnecessary public IP addresses;
- full key ARNs;
- sensitive reviewer contact information.

---

## 13. Fail-Closed Conditions

The human attestation protocol must fail closed if:

- reviewer scope is missing;
- reviewed dossier hash is missing;
- independent reproduction is claimed without independent execution or review;
- threat-model or external red-team/security review is claimed without review evidence;
- methodology review is missing;
- limitations are missing;
- claim-boundary review is missing;
- reviewer signs forbidden claims;
- reviewer attests domains not reviewed;
- automated evidence is treated as human attestation;
- external validation pass is claimed before signed human attestation.
- SLSA L4 full achievement, SLSA L4 certification, production supply-chain certification, or externally verified in-toto chain is claimed without required evidence.

---

## 14. Permitted Claim

This document defines the human attestation protocol for scoped review of the AEM-EVOLVE v4.0 Notary Dossier.

---

## 15. Non-Claims

This document does not claim:

- completed human attestation;
- completed external validation;
- completed third-party reproduction;
- completed external security review;
- completed external claim review;
- external certification;
- regulatory approval;
- cybersecurity certification;
- legal compliance;
- financial advice;
- clinical or diagnostic readiness;
- universal production readiness;
- absence of all vulnerabilities.
- SLSA L4 full achievement;
- SLSA L4 certification;
- production supply-chain certification;
- externally verified in-toto chain.
