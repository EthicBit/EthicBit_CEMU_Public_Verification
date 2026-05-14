# Public Status Bulletin — v4.0 Controlled Environment Evidence Execution

**Date:** 2026-05-12
**Version:** v4.0 Controlled Environment Evidence
**Release type:** Evidence Execution — Controlled Environment Partial
**Status:** CONTROLLED_EVIDENCE_PARTIAL
**Commit SHA (main):** `pending`
**Constitutional regime:** EthicBit / CEMU v3.7.0+
**Prerequisite baseline:** AI-ME v3.1 PASS (12/12 gates) + Fast Path v1.0 EVIDENCE_PASS (9/9 scenarios)
**v4.0 controlled evidence result:** CONTROLLED_EVIDENCE_PARTIAL — 3/8 criteria CONTROLLED_PASS, 5/8 PENDING_EXTERNAL

---

## What shipped

v4.0 controlled environment evidence execution completes the first controlled evidence pass for all 8 v4.0 acceptance criteria defined in the v4.0 External Validation Roadmap. Scope: AEM-EVOLVE multi-agent governance API — controlled environment — EthicBit / CEMU v3.7.0+.

**1. Evidence artifacts (8)** — `assurance/v4_0/evidence/`. One JSON artifact per v4.0 criterion, each declaring `controlled_status` (CONTROLLED_PASS or PENDING_EXTERNAL) with scope qualifiers and explicit non-claims.

**2. Evidence runner** — `demos/aem-evolve-multi-agent-api/tools/v4_0/run_v4_0_evidence.py`. Loads all 8 artifacts, verifies statuses against expected values, computes SHA256 fingerprints, and produces the controlled evidence report.

**3. Controlled evidence report** — `assurance/v4_0/V4_0_CONTROLLED_EVIDENCE_REPORT.json`. Status: CONTROLLED_EVIDENCE_PARTIAL. Records: 8 criteria, 3 CONTROLLED_PASS, 5 PENDING_EXTERNAL. `v4_0_external_validation_release_claimed: false`.

**4. Reproduction Kit update** — `docs/reproduction/THIRD_PARTY_REPRODUCTION_KIT_V4_0.md` updated from `SCAFFOLD` to `READY`. Prerequisites now met (v3.1 evidence complete). Quickstart updated with full execution commands.

---

## Criterion results

| # | Criterion | Controlled Status |
|---|---|---|
| 1 | Third-party reproduction | **PENDING_EXTERNAL** |
| 2 | External security review | **PENDING_EXTERNAL** |
| 3 | Managed cloud deployment | **PENDING_EXTERNAL** |
| 4 | HSM signing | **PENDING_EXTERNAL** |
| 5 | AEM v1.1 reverification | **CONTROLLED_PASS** |
| 6 | Triple Anchor verification | **CONTROLLED_PASS** |
| 7 | Fast Path benchmark | **CONTROLLED_PASS** |
| 8 | External claim review | **PENDING_EXTERNAL** |

---

## CONTROLLED_PASS details

**Criterion 5 — AEM v1.1 reverification (controlled):**
Re-verification of 12 AI-ME v3.1 evidence artifacts. SHA256 recomputed from artifact bytes; compared against `artifact_hash` in AEM v1.1 receipts. Result: 12/12 hash-match.
Non-claim: performed in the same controlled environment as original verification. External third-party reverification required for v4.0.

**Criterion 6 — Triple Anchor verification (controlled):**
Structural verification of `docs/anchors/AEM_V1_1_MAINNET_ANCHOR_RECEIPT.json`. Schema verified, required fields present, network=ethereum-mainnet, block_number=24996672, tx_hash=`0xa0a354162c5d2e2eb3a45ecd6bb34f0a57ac093d2674e5fb5eed87e4551165c0`.
Non-claim: on-chain RPC verification not performed. No new v4.0 anchor receipts created.

**Criterion 7 — Fast Path benchmark (controlled):**
9 Fast Path v1.0 verdict files measured. min=0.001ms, max=0.091ms, avg=0.013ms. `full_assurance_recomputed_this_tick=false` all scenarios.
Non-claim: controlled local environment only. Not managed cloud. Not independent measurement.

---

## PENDING_EXTERNAL criteria (5/8)

These require external parties or external infrastructure that cannot be provided in the controlled environment:

- **Third-party reproduction** — Requires independent party, separate environment
- **External security review** — Requires independent reviewer with no EthicBit affiliation
- **Managed cloud deployment** — Requires managed compute, networking, PostgreSQL, Prometheus/Grafana
- **HSM signing** — Requires `AEM_KMS_PROVIDER` in external managed environment
- **External claim review** — Requires independent reviewer to evaluate claim boundaries

---

## Full technology stack state

```
Constitutional regime:     EthicBit / CEMU v3.7.0+                  ACTIVE
Artifact Assurance:        AEM v1.1                                  ACTIVE
Governance Engine:         AEM-EVOLVE™                               ACTIVE
Evidence Baseline:         v2.0 PASS (14/14 gates, 140/140)          VERIFIED
Category Release:          AEM-EVOLVE v3.0                           RELEASED
AI-ME Gate Suite:          v3.1 PASS (12/12 gates)                   EVIDENCE PASS
Claim Boundary Engine:     Doctrine + Engine scaffold                 ACTIVE
Fast Path:                 v1.0 EVIDENCE_PASS (9/9 scenarios)        EVIDENCE PASS
Triple Anchor:             Selected artifacts anchored                ACTIVE
Strong Closure:            v2.0 governance sign-off                  ACTIVE
Reproduction Kit:          v4.0 READY                                READY
v4.0 External Validation:  CONTROLLED_EVIDENCE_PARTIAL (3/8)         CONTROLLED
```

## Key artifacts

- [v4.0 Controlled Evidence Report](../assurance/v4_0/V4_0_CONTROLLED_EVIDENCE_REPORT.json)
- [Evidence artifacts](../assurance/v4_0/evidence/)
- [Evidence runner](../demos/aem-evolve-multi-agent-api/tools/v4_0/run_v4_0_evidence.py)
- [Reproduction Kit v4.0](reproduction/THIRD_PARTY_REPRODUCTION_KIT_V4_0.md)
- [v4.0 Roadmap](strategy/AEM_EVOLVE_V4_0_EXTERNALIZED_MECHANICAL_ETHICS_ASSURANCE_ROADMAP.md)

## Claim

v4.0 controlled environment evidence execution CONTROLLED_EVIDENCE_PARTIAL (3/8 criteria CONTROLLED_PASS, 5/8 PENDING_EXTERNAL) — AEM-EVOLVE multi-agent governance API — controlled environment — EthicBit / CEMU v3.7.0+ — 2026-05-12.

## Non-claims

```
v4.0 External Validation Release NOT claimed.
Third-party reproduction NOT completed.
External security review NOT completed.
Managed cloud deployment NOT completed.
HSM-backed signing NOT configured.
External claim review NOT completed.
AEM v1.1 reverification: controlled environment only — not external party.
Triple Anchor: structural verification only — no on-chain RPC — no new v4.0 receipts.
Fast Path benchmark: controlled local environment — not managed cloud — not independent.
Not production deployment.
Not regulatory approval.
Not external certification.
```
