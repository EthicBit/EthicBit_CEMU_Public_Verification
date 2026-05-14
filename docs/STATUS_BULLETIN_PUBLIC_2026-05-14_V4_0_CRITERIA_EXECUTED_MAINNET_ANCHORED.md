# Public Status Bulletin — v4.0 All 8 Criteria Executed + Ethereum Mainnet Anchor

**Date:** 2026-05-14
**Version:** v4.0 External Validation
**Release type:** Evidence Execution Complete — Mainnet Anchor Confirmed
**Status:** EXTERNAL_VALIDATION_IN_PROGRESS
**Commit SHA (main):** `f0c7b65e`
**Tag:** `aem-evolve-v4.0-controlled-evidence-2026-05-14`
**Constitutional regime:** EthicBit / CEMU v3.7.0+
**Prior bulletin:** STATUS_BULLETIN_PUBLIC_2026-05-14_V4_0_EXTERNAL_VALIDATION_INITIATED.md
**Permitted claim:** EthicBit / AEM-EVOLVE v4.0 controlled evidence execution is complete — all 8 criteria have been executed — 3/8 CONTROLLED_PASS — 5/8 PENDING_EXTERNAL — Ethereum mainnet anchor confirmed.

---

## What changed

All 8 v4.0 acceptance criteria have been executed with controlled assessments. This is the first time all 8 criteria have a formal artifact. Criteria 5, 6, and 7 (verifiable entirely within a controlled environment) are CONTROLLED_PASS. Criteria 1, 2, 3, 4, and 8 require independent external parties and remain PENDING_EXTERNAL — each now has a controlled-tier assessment documenting what was verified internally and what requires an external party.

A new Ethereum mainnet EIP-4844 blob anchor has been confirmed, covering all 8 criterion artifacts, all 4 core evidence reports, and the current git HEAD.

---

## v4.0 Criteria — full execution state

| # | Criterion | Status | Controlled Assessment |
|---|---|---|---|
| 1 | Third-party reproduction | PENDING_EXTERNAL | CONTROLLED_SELF_REPRODUCTION_PASS |
| 2 | External security review | PENDING_EXTERNAL | CONTROLLED_ASSESSMENT_PASS_INTERNAL_CONTROLS |
| 3 | Managed cloud deployment | PENDING_EXTERNAL | CONTROLLED_ASSESSMENT_PASS_DOCUMENTATION_AND_CODE_TIER |
| 4 | HSM / KMS signing | PENDING_EXTERNAL | CONTROLLED_ASSESSMENT_PASS_SOFTWARE_SIGNING_CODE_TIER |
| 5 | AEM v1.1 reverification | CONTROLLED_PASS | — |
| 6 | Triple Anchor verification | CONTROLLED_PASS | — |
| 7 | Fast Path v1.0 benchmark | CONTROLLED_PASS | — |
| 8 | External claim review | PENDING_EXTERNAL | CONTROLLED_CLAIM_AUDIT_PASS |

---

## On-chain anchors

| Network | Block | TX | Scope |
|---|---|---|---|
| Sepolia testnet | 10840044 | 0xc5908653... | v3.1 + FastPath hashes |
| Sepolia testnet | 10852797 | 0xf26be6cc... | v4.0 all 8 criterion artifacts |
| Ethereum mainnet | 25095358 | 0xd5fe4445... | v4.0 all 8 criterion artifacts |

Mainnet explorer: https://etherscan.io/tx/0xd5fe44459f15e1cb3230f841f039d35d73da84564963fb4b32dcb9000da2cb41

---

## Criterion artifacts

All 8 artifacts are at `assurance/v4_0/evidence/` and attached to the public release:

```
V4_0_01_REPRODUCTION_KIT_ARTIFACT.json
V4_0_02_SECURITY_REVIEW_ARTIFACT.json
V4_0_03_CLOUD_DEPLOYMENT_ARTIFACT.json
V4_0_04_HSM_SIGNING_ARTIFACT.json
V4_0_05_AEM_REVERIFICATION_ARTIFACT.json
V4_0_06_TRIPLE_ANCHOR_ARTIFACT.json
V4_0_07_FAST_PATH_BENCHMARK_ARTIFACT.json
V4_0_08_CLAIM_REVIEW_ARTIFACT.json
```

---

## Public package

```
Public mirror:
https://github.com/EthicBit/EthicBit_CEMU_Public_Verification

Latest release:
https://github.com/EthicBit/EthicBit_CEMU_Public_Verification/releases/tag/aem-evolve-v4.0-controlled-evidence-2026-05-14

Third-party kit:
docs/reproduction/THIRD_PARTY_REPRODUCTION_KIT_V4_0.md

Report template:
docs/reproduction/THIRD_PARTY_REPRODUCTION_REPORT_TEMPLATE.md

Engagement package:
docs/external-validation/V4_0_EXTERNAL_VALIDATION_ENGAGEMENT_PACKAGE.md

Outreach pack:
docs/external-validation/outreach/V4_0_EXTERNAL_REVIEWER_OUTREACH_PACK.md
```

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
Triple Anchor (v3.1):      Sepolia block 10840044                    ON-CHAIN (testnet)
Triple Anchor (v4.0):      Sepolia block 10852797                    ON-CHAIN (testnet)
Triple Anchor (v4.0):      Mainnet block 25095358                    ON-CHAIN (mainnet)
Strong Closure:            v2.0 governance sign-off                  ACTIVE
Reproduction Kit:          v4.0 READY                                READY
v4.0 Criteria Executed:    8/8 — 3 CONTROLLED_PASS 5 PENDING_EXT    COMPLETE
v4.0 External Validation:  EXTERNAL_VALIDATION_IN_PROGRESS           ACTIVE
```

---

## Claim

EthicBit / AEM-EVOLVE v4.0 controlled evidence execution is complete — all 8 criteria executed — 3/8 CONTROLLED_PASS — 5/8 PENDING_EXTERNAL — Ethereum mainnet anchor confirmed block 25095358 — EthicBit / CEMU v3.7.0+ — 2026-05-14.

## Non-claims

```
v4.0 validated              — NOT claimed
third-party reproduced      — NOT claimed
externally certified        — NOT claimed
production-ready            — NOT claimed
regulatory-approved         — NOT claimed
clinical validation         — NOT claimed
financial advice            — NOT claimed
cybersecurity certification — NOT claimed
universal production-readiness — NOT claimed
mainnet anchor = validation — NOT claimed (timestamped integrity reference only)
```
