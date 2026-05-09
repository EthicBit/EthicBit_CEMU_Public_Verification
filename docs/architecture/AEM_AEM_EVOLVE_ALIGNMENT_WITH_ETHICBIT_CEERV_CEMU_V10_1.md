# AEM v1.1 and AEM-EVOLVE™ v1.1 Alignment with ETHICBIT / CEERV / CEMU v10.1

**Document type:** Architectural alignment mapping
**Version:** v1.1.0
**Status:** Architectural documentation only
**Scope:** Declared jurisdictions and declared targets only

---

## 1. Purpose

This document formally connects the historical ETHICBIT / CEERV / CEMU v10.1 assurance baseline with AEM v1.1 and AEM-EVOLVE™ v1.1.

It is architectural documentation. It does not create new production, regulatory, certification, or legal compliance claims.

---

## 2. Historical Baseline Reference

- **Source document:** `docs/history/ETHICBIT_CEERV_CEMU_V10_1_MASTER_REPO_TREE.md`
- **Factual cutoff:** 2026-04-04
- **Claim:** The v10.1 master tree documents a declared-scope EthicBit / CEERV / CEMU assurance architecture.

---

## 3. EthicBit Mechanical Ethics Assurance Stack

```
╔══════════════════════════════════════════════════════╗
║         EthicBit Mechanical Ethics Assurance Stack   ║
╠══════════════════════════════════════════════════════╣
║  EthicBit Doctrine Layer                             ║
║  (Mechanical Ethics standard / claim discipline)     ║
╠══════════════════════════════════════════════════════╣
║  CEERV Offline Verifiable Evidence Layer             ║
║  (SHA-256 manifests / evidence packages / checksums) ║
╠══════════════════════════════════════════════════════╣
║  CEMU Operational Capsule Layer                      ║
║  (Intake → Governance → Fixation → Sealing →         ║
║   Verification → Closure → Provenance →              ║
║   RuntimeGuard → Enforcement)                        ║
╠══════════════════════════════════════════════════════╣
║  AEM Artifact Assurance Layer                        ║
║  (Declared artifact verification / SLSA / in-toto)   ║
╠══════════════════════════════════════════════════════╣
║  AEM-EVOLVE™ Governed Change Assurance Layer         ║
║  (Event → Gate → Receipt → HITL → Audit)             ║
╚══════════════════════════════════════════════════════╝
```

---

## 4. Layer Alignment Table

| Layer | Historical Function (v10.1) | Evolution in AEM-EVOLVE™ v1.1 |
|---|---|---|
| **EthicBit** | Mechanical Ethics doctrine | Claim boundary discipline; lingo dictionary; non-claim enforcement |
| **CEERV** | Offline verifiable evidence | Evidence package; manifests; SHA-256 checksums; receipt integrity |
| **CEMU** | Intake, governance, fixation, sealing, closure | Operational assurance precedent for all AEM execution patterns |
| **AEM** | Artifact assurance | Declared artifact verification; SLSA L4; in-toto; Sigstore |
| **AEM-EVOLVE™** | Governed change assurance | Event → Gate → Receipt → HITL → Audit; multi-anchor verification |

---

## 5. EthicBit Doctrine Layer (v1.1)

In AEM-EVOLVE™ v1.1, the EthicBit doctrine layer manifests as:

- **Claim boundary discipline** — all v1.1 claims are bounded to declared scope
- **Lingo dictionary** (`docs/LINGO_AND_CLAIM_DICTIONARY.md`) — canonical allowed / restricted / forbidden terms
- **Non-claims** — explicit list of what v1.1 does not assert (regulatory approval, certification, legal compliance, conformity assessment, tamper-proof, HSM-backed, etc.)
- **Regulatory mapping boundary** — mapping evidence vs. approval claims are formally separated

---

## 6. CEERV Offline Verifiable Evidence Layer (v1.1)

In AEM-EVOLVE™ v1.1, the CEERV evidence layer manifests as:

- **Execution manifest** with canonical SHA-256 hash record
- **Multi-anchor verification** linking to Ethereum mainnet and triple public anchor
- **Receipt integrity** — evolution receipts are sealed, hashed, and forgery-tested
- **Evidence package** consumable without network access (offline verifiability preserved)

---

## 7. CEMU Operational Capsule Layer (v1.1)

In AEM-EVOLVE™ v1.1, the CEMU capsule pattern is the operational precedent for:

- **Intake** — governed API event intake with scope validation
- **Governance** — materiality assessment gate before execution
- **Fixation** — state fixation in evolution receipts
- **Sealing** — SHA-256 sealed receipts with demo Ed25519 signature
- **Verification** — HITL signature verification + forgery test battery
- **Closure** — fail-closed outcome on scope boundary violations
- **Provenance** — chain from event intake to signed official status
- **RuntimeGuard** — fail-closed L4 operative enforcement

---

## 8. AEM Artifact Assurance Layer (v1.1)

AEM v1.1 extends v1.0 artifact assurance with:

- SLSA Level 4 provenance records
- in-toto attestation index
- Sigstore policy reference
- Supply-chain verification manifest

---

## 9. AEM-EVOLVE™ Governed Change Assurance Layer (v1.1)

AEM-EVOLVE™ v1.1 is the top assurance layer. It adds to v1.0:

| Capability | v1.0 | v1.1 |
|---|---|---|
| Public controlled-environment release | ✓ | ✓ |
| Historical EthicBit / CEERV / CEMU baseline documented | — | ✓ |
| Regulatory mapping evidence | — | ✓ |
| Governance-effectiveness metrics | — | ✓ |
| Multi-anchor verification report | partial | ✓ |
| HITL signature verification | demo | hardened demo |
| Receipt-forgery testing | — | ✓ |
| Signed official status | — | ✓ |
| Canonical claim-language dictionary | — | ✓ |
| Whitepaper v1.1 | — | ✓ |

---

## 10. What Changed from v10.1 to AEM-EVOLVE™ v1.1

v10.1 established the doctrine, evidence, and operational capsule pattern.

AEM-EVOLVE™ v1.1 applies that pattern to governed AI change assurance at the event level, adding:

1. Regulator-mappable evidence packages (EU AI Act, NIST AI RMF, ISO/IEC 42001)
2. Quantified governance-effectiveness metrics for controlled demonstrations
3. Unified multi-anchor verification across Ethereum mainnet and triple public anchor
4. Demo HITL signature verification with explicit identity boundary
5. Receipt-forgery test battery (8 adversarial scenarios)
6. Demo Ed25519 signed official status artifact
7. Canonical lingo dictionary enforcing claim boundary discipline

---

## 11. Supported Claim

> AEM-EVOLVE™ v1.1 is the governed-change assurance layer of the broader EthicBit / CEERV / CEMU Mechanical Ethics Assurance architecture.

---

## 12. Claim Boundary

This alignment mapping is architectural documentation. It does not create new production, regulatory, certification, or legal compliance claims.

Historical v10.1 labels apply only within the declared scope. AEM-EVOLVE™ v1.1 labels apply only within the declared controlled-environment scope.

Neither layer asserts:
- Formal regulatory approval
- External certification
- Legal compliance
- Conformity assessment
- Universal production readiness
- Independent external reproduction (unless separately evidenced)
- Cybersecurity certification
- HSM-backed key custody (unless separately implemented)
- Tamper-proof storage
