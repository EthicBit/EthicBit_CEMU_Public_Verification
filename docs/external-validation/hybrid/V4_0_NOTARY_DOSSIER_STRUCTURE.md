# AEM-EVOLVE v4.0 Notary Dossier Structure

**System:** EthicBit / CEMU  
**Layer:** AEM-EVOLVE v4.0 hybrid validation support  
**Document type:** Dossier structure specification  
**Status:** `NOTARY_DOSSIER_STRUCTURE_DEFINED`  
**Depends on:** `V4_0_HYBRID_VALIDATION_SUPPORT_MODEL.md`, `V4_0_AUTOMATED_EVIDENCE_PIPELINE.md`

---

## 1. Purpose

This document defines the Notary Dossier structure for AEM-EVOLVE v4.0.

The Notary Dossier packages automated, machine-verifiable evidence into a scoped review bundle for external human reviewers. It preserves hashes, methodology, limitations, and non-claims so a reviewer can assess integrity and claim-boundary sufficiency without relying on informal narrative alone.

The dossier is a review package. It is not a certification, regulatory approval, cybersecurity audit, or third-party reproduction result by itself.

---

## 2. Core Function

The Notary Dossier converts:

```text
automated evidence artifacts
  -> scoped evidence bundle
  -> hash-verifiable review package
  -> human attestation input
```

It must not convert automated evidence directly into:

```text
EXTERNAL_VALIDATION_PASS
```

---

## 3. Dossier Location

Canonical scaffold path:

```text
assurance/external-validation/v4_0/notary_dossier/
```

Recommended dossier structure:

```text
assurance/external-validation/v4_0/notary_dossier/
- README.md
- DOSSIER_MANIFEST.json
- DOSSIER_HASH_RECORD.txt
- AUTOMATED_REPRODUCTION_REPORT.json
- AUTOMATED_SECURITY_REVIEW_SUMMARY.json
- CLAIM_BOUNDARY_RED_TEAM_REPORT.json
- CLOUD_KMS_EVIDENCE_SUMMARY.json
- ANCHOR_REFERENCE_SUMMARY.json
- METHODOLOGY_REVIEW.md
- HUMAN_ATTESTATION_TEMPLATE.md
- NON_CLAIMS.md
```

HV-2 creates the structure definition and initial scaffold files. Future PRs may generate the reports and hash records.

---

## 4. Required Metadata

A completed Notary Dossier should declare:

- dossier name;
- dossier version;
- repository reference;
- commit or tag;
- evidence scope;
- generated timestamp;
- dossier status;
- evidence artifacts included;
- hash algorithm;
- canonicalization rules;
- human attestation status;
- claim boundary status;
- limitations;
- non-claims.

---

## 5. Required Review Domains

The dossier should support human review of:

- evidence integrity;
- evidence methodology;
- hash reproducibility;
- reproduction support evidence;
- security-review support evidence;
- claim-boundary red-team evidence;
- cloud and KMS evidence scope;
- anchor-reference scope;
- limitations;
- public mirror sanitization;
- non-claims.

---

## 6. Dossier Status Vocabulary

Allowed dossier statuses:

```text
DOSSIER_STRUCTURE_DEFINED
DOSSIER_BUILT
DOSSIER_VERIFIED
DOSSIER_INCOMPLETE
DOSSIER_FAIL_CLOSED
HUMAN_ATTESTATION_PENDING
HUMAN_ATTESTATION_PARTIAL
HUMAN_ATTESTATION_PASS
```

Forbidden status for automated dossier builders:

```text
EXTERNAL_VALIDATION_PASS
```

Only scoped human attestation plus claim-state governance may support external-validation elevation.

---

## 7. Minimum Scaffold Files

HV-2 introduces these scaffold files:

```text
assurance/external-validation/v4_0/notary_dossier/README.md
assurance/external-validation/v4_0/notary_dossier/DOSSIER_MANIFEST.json
assurance/external-validation/v4_0/notary_dossier/NON_CLAIMS.md
assurance/external-validation/v4_0/notary_dossier/HUMAN_ATTESTATION_TEMPLATE.md
```

These files define the structure and review boundary. They do not indicate that a dossier has been completed or attested.

---

## 8. Public Mirror Sanitization

The public verification mirror may publish dossier summaries and hash-verifiable evidence references.

Public dossier material must avoid exposing unnecessary operational details such as:

- secrets;
- private keys;
- database credentials;
- database endpoints;
- public IP addresses;
- account IDs;
- security group IDs;
- full key ARNs;
- non-public infrastructure configuration.

Sanitized evidence may include provider class, region, service category, check status, hash records, receipts, and non-sensitive verification summaries.

---

## 9. Fail-Closed Conditions

The dossier process must fail closed if:

- required dossier metadata is missing;
- included evidence hashes do not match;
- JSON evidence is invalid;
- public evidence exposes sensitive private operational identifiers;
- claim-boundary red-team evidence is missing;
- human attestation is claimed but not present;
- external validation pass is claimed by an automated process;
- non-claims are omitted.

---

## 10. Permitted Claim

This document defines the Notary Dossier structure for packaging automated evidence into a hash-verifiable review bundle.

---

## 11. Non-Claims

This document does not claim:

- a completed Notary Dossier;
- completed human attestation;
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
- external validation pass.
