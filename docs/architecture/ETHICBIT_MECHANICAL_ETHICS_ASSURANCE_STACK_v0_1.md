# EthicBit Mechanical Ethics Assurance for AI Stack v0.1

## Purpose

This document defines the public architecture hierarchy for the current EthicBit/CEMU Mechanical Ethics Assurance for AI stack.

It consolidates the verified layers already present in the repository without changing the canonical AEM V1.1 artifact, the AEM-EVOLVE technical demonstration release, the supply-chain verification extension, the reproducibility extension, or their existing Ethereum mainnet anchors.

## Official Hierarchy

### Layer 1 - Artifact Assurance

AEM V1.1 verifies the artifact.

Primary references:

- `docs/AGENTE_ETICO_MECANICO_V1_1.md`
- `registry/ETHICBIT_CEMU_AEM_V1_1_GLOBAL_PUBLIC_VERIFICATION_REGISTRY.json`
- `receipts/ETHICBIT_CEMU_AEM_V1_1_GLOBAL_PUBLIC_VERIFICATION_REGISTRY_MAINNET_ANCHOR_RECEIPT.json`

### Layer 2 - Governed Evolution Assurance

AEM-EVOLVE governs the change.

Primary references:

- `docs/evolve/AEM_EVOLVE_CONCEPT_PAPER_v0_3.md`
- `assurance/evolve/AEM_EVOLVE_MANIFEST.json`
- `receipts/AEM_EVOLVE_TECHNICAL_DEMONSTRATION_MAINNET_ANCHOR_RECEIPT.json`

### Layer 3 - Public Evidence Surface

GitHub exposes the evidence.

Primary references:

- public repository: `EthicBit/EthicBit_CEMU`
- release tag: `aem-evolve-technical-demonstration-v0.3-2026-05`
- release tag: `aem-v1.1-independent-reproduction-challenge-external-ready-2026-05-02`

### Layer 4 - Integrity Anchoring

Ethereum mainnet anchors the integrity.

Primary references:

- AEM V1.1 Global Registry anchor receipt
- AEM V1.1 Supply-Chain Verification Extension anchor receipt
- AEM V1.1 Reproducibility Extension anchor receipt
- AEM-EVOLVE Technical Demonstration anchor receipt

### Layer 5 - Supply-Chain Assurance

SLSA-style posture supports supply-chain assurance.

Primary references:

- `docs/supply-chain/AEM_V1_1_SUPPLY_CHAIN_VERIFICATION_EXTENSION.md`
- `assurance/provenance/SLSA_PROVENANCE.json`
- `assurance/in-toto/attestation-index.json`
- `assurance/release/AEM_V1_1_SUPPLY_CHAIN_VERIFICATION_MANIFEST.json`
- `scripts/verify_release.sh`

### Layer 6 - Runtime Secret Protection

ML-KEM768 + X25519 protects runtime secrets.

Primary references:

- `docs/crypto/MLKEM768_RUNTIME_SECRET_PROTECTION.md`
- `assurance/crypto/pq_kem.go`
- `mechanical_ethics/gate.go`
- `results/pq_runtime_secret_protection.json`

### Layer 7 - Scope Boundary Layer

Scope boundaries prevent overclaiming.

Primary references:

- `docs/third_party_representation_boundary.md`
- `docs/evolve/AEM_EVOLVE_RELEASE_SCOPE_BOUNDARY.md`
- `docs/crypto/MLKEM768_RUNTIME_SECRET_PROTECTION.md`
- `results/legal_claim_boundary.md`

## Current Public Claim

EthicBit/CEMU provides a GitHub-inspectable, scope-delimited, public-verifiable Mechanical Ethics Assurance stack for AI, including artifact assurance, governed evolution assurance, public evidence surfaces, Ethereum mainnet integrity anchors, SLSA-style supply-chain posture, ML-KEM768 + X25519 runtime secret protection, and explicit scope boundaries.

## Future Unified Anchor Path

The unified manifest associated with this architecture is:

`assurance/unified/ETHICBIT_MECHANICAL_ETHICS_ASSURANCE_UNIFIED_MANIFEST_v0_1.json`

After this architecture and manifest are merged to `main`, the manifest may be anchored on Ethereum mainnet. The anchor receipt must be added separately and must not mutate the manifest that was anchored.

## Explicit Non-Claims

This architecture does not claim:

- regulatory approval;
- clinical validation;
- diagnostic authorization;
- production readiness;
- lab readiness;
- full SLSA L4 certification;
- FIPS module validation;
- cryptographic module certification;
- absolute quantum security;
- independent reproduction completed;
- automatic third-party binding;
- FDA/EMA acceptance;
- GxP certification.
