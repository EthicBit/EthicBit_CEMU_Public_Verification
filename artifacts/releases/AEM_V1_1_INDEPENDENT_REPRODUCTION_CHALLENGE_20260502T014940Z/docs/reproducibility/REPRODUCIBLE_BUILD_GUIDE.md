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
git checkout aem-v1.1-global-registry-final-2026-05-01
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

