# Programmatic Anchor Policy

**Version:** 1.0  
**Date:** 2026-05-18  
**Status:** ACTIVE  
**Machine-readable policy:** `assurance/anchor/anchor-policy.json`

## Purpose

Defines when, where, and under what conditions EthicBit/CEMU artifacts are
anchored to public networks. Anchoring provides tamper-evident timestamping
and public verifiability within declared scope — it does not constitute
certification, regulatory approval, or proof of correctness.

---

## Anchor Networks

| Network | Role | Type |
|---------|------|------|
| **Sepolia** | Public tamper evidence (testnet EVM) | Triple Public Anchor |
| **Arweave** | Permanent decentralized storage | Triple Public Anchor |
| **AO** | Arweave compute layer message | Triple Public Anchor |
| **Ethereum Mainnet** | Production provenance | EIP-4844 KZG blob (type-3 TX) |

The **Triple Public Anchor** = Sepolia + Arweave + AO. Bitcoin is excluded from the canonical set (legacy planning reference only).

---

## Signing Keys (pre-anchor requirements)

| Key | Alias | Purpose |
|-----|-------|---------|
| in-toto / artifact signing | `alias/ethicbit-intoto-signing` | in-toto statements, SBOM, build manifests |
| Runtime API | `alias/ethicbit-kms-signing` | API runtime only — **not** used for anchoring |

---

## Release Classes and Anchor Requirements

### DEVELOPMENT
No anchor required. Local and CI runs.

### CONTROLLED_EVIDENCE
- **Networks:** Triple Public Anchor  
- **Prerequisites:** SBOM KMS-signed, claim boundary 100% BLOCKED  
- **Human review:** not required  
- **Current status:** ✓ satisfied (v4.0 anchored 2026-05-14)

### EXTERNAL_VALIDATION ← *current class*
- **Networks:** Triple Public Anchor + Mainnet KZG blob  
- **Prerequisites:** All CONTROLLED_EVIDENCE prerequisites, plus in-toto chain KMS-signed, `slsa-build.yml` active  
- **Human review:** not required  
- **Current status:** All prerequisites met. Next anchor operation should use this class.

### PRODUCTION_RELEASE
- **Networks:** Triple Public Anchor + Mainnet KZG blob  
- **Prerequisites:** All EXTERNAL_VALIDATION prerequisites, plus in-toto externally witnessed, `human_attestation_status = HUMAN_ATTESTED`, 5/8 external validation criteria minimum  
- **Human review:** **required** before anchor execution  
- **Current status:** blocked on external witness + human attestation

---

## Release Gates

| Gate | Script/Workflow | Blocks |
|------|----------------|--------|
| Triple anchor reconciliation | `deployment/anchor_pre_deploy_gate.sh` | CE, EV, PR |
| Claim boundary 100% blocked | `tools/.../run_claim_red_team.py` + CI workflow | CE, EV, PR |
| KMS signatures present | Check sidecar files | EV, PR |
| Human review sign-off | Manual — no script | PR only |

---

## Current Anchor State (2026-05-18)

| Check | Status |
|-------|--------|
| SBOM KMS-signed | ✓ `2026-05-18T02:52:13Z` |
| in-toto chain KMS-signed (6/6) | ✓ `2026-05-18T02:39:56Z` |
| in-toto externally witnessed | ✗ pending external validator |
| SLSA build workflow active | ✓ `slsa-build.yml` |
| Claim boundary (14/14 BLOCKED) | ✓ 100% |
| Triple public anchor (last) | ✓ 2026-05-14 (v4.0 controlled evidence) |
| Mainnet KZG blob (last) | ✓ 2026-05-14 (v4.0 controlled evidence) |
| Human attestation | ✗ HUMAN_ATTESTATION_PENDING |

**Release class eligible for next anchor:** `EXTERNAL_VALIDATION`

---

## Non-Claims

- Anchoring does **not** prove correctness of the anchored content.  
- Anchoring does **not** constitute external certification or regulatory approval.  
- Triple Public Anchor is **tamper-evident**, not tamper-proof storage.  
- Mainnet anchor is **not** regulatory approval.
