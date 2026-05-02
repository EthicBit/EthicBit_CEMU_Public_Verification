# AEM V1.1 Reproducible Build Guide

## Purpose
This guide describes how an independent reviewer can reproduce declared release subjects from a clean environment and compare outputs against official expected hashes.

## Current Claim
Current closure:

`PUBLIC_REPRODUCIBLE_VERIFICATION_SUPPORT`

Target closure:

`INDEPENDENTLY_REPRODUCED_RELEASE_BUILD`

## Scope
This guide supports declared-subject reproduction. It does not claim universal deterministic rebuild for all repository outputs.

## Declared Subjects
The declared subjects for this challenge are:

- `global_public_verification_registry`: canonical JSON hash of the AEM V1.1 Global Public Verification Registry.
- `supply_chain_manifest`: canonical JSON hash of the Supply-Chain Verification Extension manifest.
- `slsa_provenance`: raw file SHA-256 of the published SLSA provenance artifact.
- `toolchain_fingerprint`: raw file SHA-256 of the published toolchain fingerprint.

Only these declared subjects are in scope for this challenge.

## Environment Notes
The operator pre-send validation was performed on macOS and inside Docker Desktop. External reviewers may use Linux or another clean environment.

Docker is recommended for reviewer execution because it reduces host-specific differences. Any host-specific deviation should be recorded in `assurance/reproducibility/environment_fingerprint.json` and the independent reproduction report.

## Requirements
- Git
- Bash
- Python 3.x
- Docker or devcontainer (recommended)
- Optional: Nix

## Steps
1. Clone repository:
```bash
git clone https://github.com/EthicBit/EthicBit_CEMU.git
cd EthicBit_CEMU
```

2. Checkout release reference:
```bash
git checkout aem-v1.1-independent-reproduction-challenge-2026-05-02
```

3. Inspect declared subjects:
```bash
cat assurance/reproducibility/declared_subjects.json
```

4. Inspect expected hashes:
```bash
cat assurance/reproducibility/expected_hashes.json
```

5. Run reproducibility flow:
```bash
bash scripts/reproducibility/build_from_clean_environment.sh
```

6. Review outputs:
```bash
cat assurance/reproducibility/comparison_report.json
cat assurance/reproducibility/independent_reproduction_report.json
```

## Important Limitation
A successful local comparison does not automatically mean independent reproduction has been achieved. Independent reproduction requires execution in a separate environment or by a third-party verifier.

SLSA provenance and in-toto style attestations may be expanded in future supply-chain work. This guide does not claim SLSA L4 certification, full security certification, or universal reproducibility.
