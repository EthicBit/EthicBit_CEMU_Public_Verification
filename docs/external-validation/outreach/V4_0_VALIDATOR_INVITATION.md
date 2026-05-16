# v4.0 External Validator Invitation

**Ready to send — copy, personalize [name], and send**
**Date:** 2026-05-16
**Current state machine:** `HYBRID_VALIDATION_READY → HUMAN_ATTESTATION_PENDING`
**Purpose:** Hybrid validation review for Criterion 1 (reproduction), Criterion 2 (security review), and Criterion 8 (claim review)
**Criteria status:** 5/8 CONTROLLED_PASS — 3/8 PENDING_EXTERNAL (criteria 1, 2, 8)

---

## Current Validation Model

EthicBit v4.0 now uses a hybrid validation support model:

```text
automated pipelines generate machine-verifiable evidence
+ external reviewers attest integrity, methodology, scope, and claim boundaries
= scoped human-attested validation support
```

Your role is not to manually rebuild the entire stack from scratch unless you choose to do so.

Your role is to review the Notary Dossier, recompute selected hashes, inspect the automated evidence methodology, evaluate claim boundaries, and issue a scoped `PASS / PARTIAL / FAIL` attestation.

The project is currently at:

```text
HYBRID_VALIDATION_READY → HUMAN_ATTESTATION_PENDING
```

5/8 criteria are CONTROLLED_PASS. Criteria 1, 2, and 8 are PENDING_EXTERNAL — awaiting your attestation.

This review supports the transition toward `EXTERNAL_VALIDATION_PASS`. It does not itself claim `EXTERNAL_VALIDATION_PASS` until an external reviewer completes and signs a scoped attestation.

---

## Invitation Message (Email / LinkedIn / Forum / DM)

Subject: Invitation — Hybrid Validation Review of EthicBit / AEM-EVOLVE AI Governance Evidence

Hi [name],

I'd like to invite you to perform a scoped external review of EthicBit / AEM-EVOLVE — a governance assurance engine for multi-agent AI systems.

**What it is:**
EthicBit / AEM-EVOLVE provides a formal evidence stack for AI governance: mechanical ethics assurance, artifact integrity verification, claim boundary enforcement, on-chain anchoring, automated reproduction support, automated security-review support, and scoped human attestation.

**Current status:**
The project has controlled evidence for selected v4.0 criteria, and now uses a hybrid validation support model. Automated pipelines generate machine-verifiable evidence, while an external reviewer evaluates the Notary Dossier and attests integrity, methodology, scope, and claim-boundary sufficiency.

**What I'm asking:**
Please review the v4.0 Notary Dossier and supporting automated evidence. You may recompute selected hashes, inspect the methodology, review the automated reproduction and security-support reports, evaluate the claim-boundary red-team evidence, and complete a scoped human attestation.

This typically takes 30–60 minutes for a scoped review.

**Your review may cover:**
- Criterion 1: reproduction support methodology and selected hash verification;
- Criterion 2: automated security-review support and limitations;
- Criterion 8: claim-boundary review and overclaim prevention;
- the Notary Dossier as a scoped review bundle.

**Suggested local commands:**

```bash
git clone https://github.com/EthicBit/EthicBit_CEMU_Public_Verification
cd EthicBit_CEMU_Public_Verification

python3 tools/external_validation/verify_v4_notary_dossier.py --structure-only
python3 tools/external_validation/automated_reproduction/verify_automated_reproduction_report.py
python3 tools/external_validation/security_review/verify_automated_security_review_summary.py
python3 tools/external_validation/claim_red_team/verify_claim_red_team_report.py
```

If the public mirror tag has not yet been refreshed with the hybrid dossier artifacts, I will provide the current review bundle or updated release link directly.

**Primary review materials:**

```text
docs/external-validation/hybrid/V4_0_HYBRID_VALIDATION_SUPPORT_MODEL.md
docs/external-validation/hybrid/V4_0_HUMAN_ATTESTATION_PROTOCOL.md
docs/external-validation/hybrid/V4_0_NOTARY_DOSSIER_STRUCTURE.md
assurance/external-validation/v4_0/notary_dossier/DOSSIER_MANIFEST.json
assurance/external-validation/v4_0/automated_reproduction/AUTOMATED_REPRODUCTION_REPORT.json
assurance/external-validation/v4_0/security_review/AUTOMATED_SECURITY_REVIEW_SUMMARY.json
assurance/external-validation/v4_0/claim_red_team/CLAIM_BOUNDARY_RED_TEAM_REPORT.json
```

**Public mirror:**
https://github.com/EthicBit/EthicBit_CEMU_Public_Verification

**Current public controlled-evidence release:**
https://github.com/EthicBit/EthicBit_CEMU_Public_Verification/releases/tag/aem-evolve-v4.0-controlled-evidence-2026-05-14

**Scope boundary:**
This is not a request for certification, regulatory approval, cybersecurity certification, legal opinion, clinical validation, financial advice, or endorsement. It is a scoped technical review of evidence integrity, methodology, limitations, and claim boundaries.

A valid outcome may be `PASS`, `PARTIAL`, or `FAIL`. Deviations, failures, and limitations are useful evidence and should be recorded.

Would you be open to this review? Happy to answer any questions or send the latest review bundle.

[Your name]
[Contact]

---

## Short Version (Forum / GitHub Discussions / Twitter/X)

We are seeking external reviewers for EthicBit / AEM-EVOLVE v4.0 hybrid validation support.

What: Review a Notary Dossier containing automated reproduction support, automated security-review support, claim-boundary red-team evidence, hashes, methodology, and non-claims.

Reviewer task: recompute selected hashes, inspect methodology, evaluate scope and claim boundaries, and issue a scoped `PASS / PARTIAL / FAIL` attestation.

Time: ~30–60 min
Environment: Your own machine or cloud instance

Repo: https://github.com/EthicBit/EthicBit_CEMU_Public_Verification
Current controlled-evidence release: `aem-evolve-v4.0-controlled-evidence-2026-05-14`

This is not a request for regulatory approval, certification, endorsement, or legal opinion. It is a scoped technical review of evidence integrity, methodology, limitations, and claim boundaries.

---

## What To Tell Reviewers About Each Criterion

| Reviewer profile | Criteria they can cover | Review focus |
|---|---|---|
| Python developer | Criterion 1 | Automated reproduction support, selected hash recomputation, script verification |
| Security engineer | Criteria 1 + 2 | Reproduction support plus automated security-review support and limitations |
| AI auditor / governance reviewer | Criteria 1 + 8 | Reproduction support plus claim-boundary review |
| Security + AI governance reviewer | Criteria 1 + 2 + 8 | Full hybrid dossier review within declared scope |
| Legal / compliance reviewer | Criterion 8 only | Claim boundary sufficiency and non-claim clarity, not legal approval |

---

## Suggested Reviewer Checklist

- [ ] I reviewed the declared scope of the v4.0 hybrid validation support model.
- [ ] I reviewed the Notary Dossier manifest.
- [ ] I recomputed selected hashes or verified hash records.
- [ ] I inspected the automated reproduction support methodology.
- [ ] I inspected the automated security-review support methodology.
- [ ] I inspected the claim-boundary red-team evidence.
- [ ] I reviewed the non-claims and limitations.
- [ ] I recorded deviations, uncertainty, or missing evidence.
- [ ] I issued a scoped `PASS / PARTIAL / FAIL` attestation.
- [ ] I did not elevate automated evidence into external certification or regulatory approval.

---

## Tracking Responses

When a reviewer agrees, record:

| Field | Value |
|---|---|
| Reviewer name / org | |
| Criteria they will cover | |
| Date agreed | |
| Environment they will use | |
| Expected completion date | |
| Dossier version / hash reviewed | |
| Report received | Y / N |
| Attestation result | PASS / PARTIAL / FAIL |
| Limitations recorded | Y / N |

---

## Non-Claim

Sending this invitation does not satisfy third-party reproduction, external security review, external claim review, external validation, external certification, cybersecurity certification, regulatory approval, legal compliance, financial advice, clinical readiness, or universal production readiness.

External validation status may only be elevated after a scoped external reviewer completes and signs an attestation covering integrity, methodology, scope, limitations, and claim boundaries.
