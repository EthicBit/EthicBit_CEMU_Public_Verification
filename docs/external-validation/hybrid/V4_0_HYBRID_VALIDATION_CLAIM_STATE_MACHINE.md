# AEM-EVOLVE™ v4.0 — Hybrid Validation Claim State Machine

**Document ID:** HV-10  
**Date:** 2026-05-16  
**Status:** ACTIVE  
**Constitutional dependency:** EthicBit/CEMU/v3.7.0+

---

## Purpose

This document defines the permitted states, valid transitions, and prohibited transitions for the AEM-EVOLVE™ v4.0 Hybrid Validation Support Architecture.

The state machine governs how controlled evidence advances toward external validation. It ensures that no automated pipeline, script, or tooling artifact may self-elevate the claim status to `EXTERNAL_VALIDATION_PASS` without a signed human attestation.

---

## Permitted States

| State | Description |
|---|---|
| `CONTROLLED_EVIDENCE_PARTIAL` | Some controlled criteria pass; infrastructure not fully provisioned |
| `CONTROLLED_EVIDENCE_ADVANCED` | All internally addressable criteria at CONTROLLED_PASS; external criteria pending |
| `HYBRID_VALIDATION_READY` | Notary Dossier built, automated pipelines pass, human attestation package complete |
| `DOSSIER_BUILT` | Notary Dossier assembled from controlled evidence artifacts |
| `DOSSIER_VERIFIED` | Dossier hashes independently verified by tooling |
| `HUMAN_ATTESTATION_PENDING` | External reviewer has received dossier; attestation not yet submitted |
| `HUMAN_ATTESTATION_PARTIAL` | External reviewer submitted scoped attestation covering subset of criteria |
| `HUMAN_ATTESTATION_PASS` | External reviewer submitted full scoped attestation — PASS within declared scope |
| `EXTERNAL_VALIDATION_SCOPE_LIMITED` | Human attestation complete for subset of criteria; remaining criteria still pending |
| `EXTERNAL_VALIDATION_PASS` | All required criteria attested by independent external reviewer(s) |
| `FAIL_CLOSED` | Evidence integrity failure, overclaim detected, or prohibited transition attempted |

---

## Valid Transitions

```
CONTROLLED_EVIDENCE_PARTIAL
  → CONTROLLED_EVIDENCE_ADVANCED       (when all internally addressable criteria reach CONTROLLED_PASS)

CONTROLLED_EVIDENCE_ADVANCED
  → HYBRID_VALIDATION_READY            (when Notary Dossier built + automated pipelines pass)

HYBRID_VALIDATION_READY
  → DOSSIER_BUILT                      (automated dossier assembly complete)
  → HUMAN_ATTESTATION_PENDING          (reviewer has received and accepted dossier)

DOSSIER_BUILT
  → DOSSIER_VERIFIED                   (hash verification confirmed by tooling)
  → DOSSIER_BUILT                      (rebuild on evidence update)

DOSSIER_VERIFIED
  → HUMAN_ATTESTATION_PENDING          (dossier delivered to reviewer)

HUMAN_ATTESTATION_PENDING
  → HUMAN_ATTESTATION_PARTIAL          (reviewer returns scoped partial attestation)
  → HUMAN_ATTESTATION_PASS             (reviewer returns full scoped attestation)
  → HUMAN_ATTESTATION_PENDING          (reviewer requests additional evidence)

HUMAN_ATTESTATION_PARTIAL
  → EXTERNAL_VALIDATION_SCOPE_LIMITED  (partial attestation accepted for declared scope)
  → HUMAN_ATTESTATION_PASS             (additional criteria attested)

HUMAN_ATTESTATION_PASS
  → EXTERNAL_VALIDATION_SCOPE_LIMITED  (criteria subset fully attested)
  → EXTERNAL_VALIDATION_PASS           (all required criteria fully attested)

EXTERNAL_VALIDATION_SCOPE_LIMITED
  → EXTERNAL_VALIDATION_PASS           (remaining criteria attested by external reviewer)

Any state
  → FAIL_CLOSED                        (on evidence integrity failure or overclaim detection)
```

---

## Minimum Conditions for `EXTERNAL_VALIDATION_PASS`

All of the following must be true before the status may be elevated to `EXTERNAL_VALIDATION_PASS`:

| Condition | Required value |
|---|---|
| `signed_human_attestation` | `true` |
| `reviewer_scope_declared` | `true` |
| `dossier_hashes_verified` | `true` |
| `methodology_review_completed` | `true` |
| `claim_boundary_review_completed` | `true` |
| `limitations_declared` | `true` |
| `no_forbidden_claims` | `true` |
| `reviewer_affiliation` | None (independent — no EthicBit affiliation) |
| `attestation_format` | Signed report or typed attestation with date and scope declaration |

---

## Prohibited Transitions

The following transitions are **permanently prohibited**. Any system, pipeline, or artifact that attempts these transitions must be treated as `FAIL_CLOSED`.

| From | To | Reason |
|---|---|---|
| `CONTROLLED_EVIDENCE_ADVANCED` | `EXTERNAL_VALIDATION_PASS` | No human attestation |
| `HYBRID_VALIDATION_READY` | `EXTERNAL_VALIDATION_PASS` | No human attestation |
| `DOSSIER_BUILT` | `EXTERNAL_VALIDATION_PASS` | No human attestation |
| `DOSSIER_VERIFIED` | `EXTERNAL_VALIDATION_PASS` | No human attestation |
| `HUMAN_ATTESTATION_PENDING` | `EXTERNAL_VALIDATION_PASS` | Attestation not received |

---

## Prohibited Claim Elevations from Automated Outputs

No automated pipeline output may be used to claim the following without independent human attestation:

| Automated output | Prohibited claim |
|---|---|
| `AUTOMATED_REPRODUCTION_SUPPORT=PASS` | `third_party_reproduction_completed` |
| `AUTOMATED_SECURITY_REVIEW_SUPPORT=PASS` | `cybersecurity_certified` |
| `AUTOMATED_SECURITY_REVIEW_SUPPORT=PASS` | `absence_of_all_vulnerabilities` |
| `CLAIM_BOUNDARY_RED_TEAM=PASS` | `external_claim_review_completed` |
| `FAST_PATH_EVIDENCE_PASS` | `full_system_sub_15ms_validation` |
| `TRIPLE_ANCHOR_PRESENT` | `universal_public_anchoring` |
| `DOSSIER_VERIFIED` | `externally_certified` |
| `DOSSIER_VERIFIED` | `regulatory_approved` |
| Any controlled evidence | `production_ready` (without managed compute + external security review) |

---

## Critical Rule

> **No automated pipeline may transition directly to `EXTERNAL_VALIDATION_PASS`.**
>
> The only valid path to `EXTERNAL_VALIDATION_PASS` is through a signed human attestation from an independent reviewer with no EthicBit affiliation, covering the declared scope, with methodology review, claim boundary review, and limitations declared.

---

## Current State (2026-05-16)

```
CONTROLLED_EVIDENCE_ADVANCED  →  HYBRID_VALIDATION_READY  →  HUMAN_ATTESTATION_PENDING
```

- Controlled criteria: 5/8 CONTROLLED_PASS
- Pending external criteria: 3/8 (criteria 1, 2, 8)
- Notary Dossier: BUILT
- Automated pipelines: PASS (reproduction, security review, claim red-team)
- Human attestation: PENDING (no reviewer has submitted attestation)

**`EXTERNAL_VALIDATION_PASS` has not been reached and is not claimed.**

---

## Claim

This document defines the hybrid validation claim state machine that governs status transitions from controlled evidence to human-attested external validation.

## Non-Claim

This document does not claim that `EXTERNAL_VALIDATION_PASS` has been reached. It does not claim completed third-party reproduction, completed external security review, completed external claim review, external certification, regulatory approval, cybersecurity certification, legal compliance, financial advice, clinical readiness, universal production readiness, absence of all vulnerabilities, full-system sub-15ms validation, or universal public anchoring.

---

## Relationship to HV Suite

| Document | Role in state machine |
|---|---|
| HV-0 Hybrid Validation Support Model | Defines the architecture |
| HV-1 Automated Evidence Pipeline | Drives `CONTROLLED_EVIDENCE_ADVANCED → HYBRID_VALIDATION_READY` |
| HV-2 Notary Dossier Structure | Defines `DOSSIER_BUILT` artifact |
| HV-3 Human Attestation Protocol | Defines conditions for `HUMAN_ATTESTATION_PASS` |
| HV-4 Notary Dossier Builder | Executes `DOSSIER_BUILT → DOSSIER_VERIFIED` |
| HV-5 Automated Reproduction Support | Contributes to `HYBRID_VALIDATION_READY` (not to `EXTERNAL_VALIDATION_PASS`) |
| HV-6 Automated Security Review Support | Contributes to `HYBRID_VALIDATION_READY` (not to `EXTERNAL_VALIDATION_PASS`) |
| HV-7 Claim Boundary Red-Team | Enforces `no_forbidden_claims=true` |
| HV-8 Validator Invitation | Initiates `HUMAN_ATTESTATION_PENDING` |
| HV-9 Status Bulletin | Records current state |
| **HV-10 Claim State Machine** | **Governs all transitions — this document** |
