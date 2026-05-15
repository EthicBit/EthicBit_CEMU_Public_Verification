# AEM-EVOLVE v4.0 Hybrid Validation Support Model

**System:** EthicBit / CEMU  
**Layer:** AEM-EVOLVE v4.0 external validation support  
**Document type:** Architecture model  
**Status:** `HYBRID_VALIDATION_SUPPORT_MODEL_DEFINED`  
**Current evidence posture:** `CONTROLLED_EVIDENCE_PARTIAL`  
**Controlled evidence criteria:** `5/8 CONTROLLED_PASS`  
**Pending external criteria:** `3/8 PENDING_EXTERNAL`

---

## 1. Purpose

This document defines the AEM-EVOLVE v4.0 Hybrid Validation Support Model.

The model combines:

- machine-verifiable evidence artifacts;
- hash-verifiable dossier packaging;
- scoped human attestation;
- claim-state governance;
- explicit non-claims and fail-closed boundaries.

The purpose is to convert controlled internal evidence into a structured external-review package without allowing automated evidence to self-elevate into external validation claims.

---

## 2. Current Status

AEM-EVOLVE v4.0 currently has controlled evidence for five of eight validation criteria:

```text
CONTROLLED_PASS:
- managed_cloud_deployment
- hsm_signing
- aem_v1_1_reverification
- triple_anchor_verification
- fast_path_benchmark

PENDING_EXTERNAL:
- third_party_reproduction
- external_security_review
- external_claim_review
```

Current status:

```text
CONTROLLED_EVIDENCE_PARTIAL
```

Target operational preparation status:

```text
HYBRID_VALIDATION_READY
```

External validation can only be claimed after scoped human review and attestation.

---

## 3. Model Summary

The Hybrid Validation Support Model uses the following flow:

```text
controlled evidence
  -> automated evidence pipeline
  -> hash-verifiable Notary Dossier
  -> scoped human review
  -> human attestation
  -> claim-state governance
  -> permitted external-validation claim, if conditions are met
```

The system does not self-certify.

The system generates evidence, preserves integrity, records scope, and prevents claim elevation unless required external human attestation exists.

---

## 4. Core Components

### 4.1 Machine-Verifiable Evidence

Machine-verifiable evidence includes JSON reports, manifests, hash records, receipts, logs, verification outputs, benchmark reports, anchor receipts, and reproducibility evidence.

This evidence may support external review, but it does not by itself constitute external validation.

### 4.2 Automated Evidence Pipelines

Automated pipelines may generate support artifacts for:

- reproduction support;
- security-review support;
- claim-boundary red-team review;
- infrastructure evidence review;
- signing and key-management evidence review;
- anchor-reference review.

Pipeline outputs are treated as support evidence only.

### 4.3 Notary Dossier

The Notary Dossier packages evidence into a scoped, hash-verifiable review bundle.

A dossier may include:

- dossier manifest;
- dossier hash record;
- automated reproduction support report;
- automated security-review support summary;
- claim-boundary red-team report;
- cloud and KMS evidence summaries;
- anchor reference summary;
- methodology review notes;
- human attestation template;
- explicit non-claims.

A dossier can be built and verified without claiming external validation.

### 4.4 Human Attestation

Human attestation is the review layer that evaluates integrity, methodology, scope, limitations, and claim-boundary sufficiency.

The reviewer does not need to certify the entire EthicBit system. The reviewer attests only the declared scope.

### 4.5 Claim-State Governance

Claim-state governance prevents unsupported status escalation.

No automated pipeline may transition directly to:

```text
EXTERNAL_VALIDATION_PASS
```

External-validation claims require scoped human attestation and declared reviewer scope.

---

## 5. Evidence-to-Claim Boundary

Automated evidence may support these claims:

```text
controlled evidence generated
machine-verifiable evidence available
hash-verifiable dossier prepared
external review package ready
human attestation pending
```

Automated evidence must not support these claims by itself:

```text
third-party reproduction completed
external security review completed
external claim review completed
external certification achieved
cybersecurity certified
regulatory approved
clinical or diagnostic ready
universal production ready
external validation pass achieved
```

---

## 6. Required Human Review Domains

The human reviewer should evaluate:

- evidence integrity;
- evidence methodology;
- hash reproducibility;
- scope boundaries;
- limitations;
- non-claims;
- claim-state transitions;
- whether external validation status is permitted within the declared scope.

The reviewer may return:

```text
PASS
PARTIAL
FAIL
OUT_OF_SCOPE
```

---

## 7. Fail-Closed Conditions

The hybrid validation process must fail closed if:

- dossier hashes do not match;
- required evidence is missing;
- reviewer scope is undeclared;
- human attestation is missing;
- claim-boundary review is missing;
- limitations are not declared;
- forbidden claims are present;
- automated evidence attempts to claim external validation directly.

---

## 8. Public Mirror Sanitization

The public verification mirror may publish sanitized evidence summaries.

Public evidence should avoid unnecessary operational exposure, including:

- database endpoints;
- public IP addresses;
- account IDs;
- security group IDs;
- full key ARNs;
- secrets;
- private keys;
- private infrastructure configuration.

The public mirror may publish provider class, region, service type, evidence status, checks performed, hash records, and non-sensitive verification summaries.

---

## 9. Permitted Claim

This document defines the AEM-EVOLVE v4.0 Hybrid Validation Support Model: automated evidence generation combined with scoped human attestation and claim-state governance.

---

## 10. Non-Claims

This document does not claim:

- completed external validation;
- completed third-party reproduction;
- completed external security review;
- completed external claim review;
- external certification;
- regulatory approval;
- cybersecurity certification;
- financial advice;
- clinical or diagnostic readiness;
- universal production readiness;
- legal compliance;
- absence of all vulnerabilities;
- universal public anchoring.

---

## 11. Strategic Position

The hybrid validation model is designed to move AEM-EVOLVE v4.0 from:

```text
CONTROLLED_EVIDENCE_PARTIAL
```

toward:

```text
HYBRID_VALIDATION_READY
```

and then, only after scoped human attestation, toward:

```text
EXTERNAL_VALIDATION_SCOPE_LIMITED
```

or:

```text
EXTERNAL_VALIDATION_PASS
```

within a declared scope.

The model preserves the central EthicBit rule:

```text
Evidence before claims.
```
