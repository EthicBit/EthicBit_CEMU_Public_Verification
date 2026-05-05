# AEM V1.1 Independent Reproduction Challenge

## Purpose
This challenge pack enables an independent reviewer to attempt reproduction of declared AEM V1.1 release subjects from a public repository reference and compare resulting hashes against official expected hashes.

## Current Closure
`PUBLIC_REPRODUCIBLE_VERIFICATION_SUPPORT`

## Target Closure
`INDEPENDENTLY_REPRODUCED_RELEASE_BUILD`

## Important Scope Boundary
This challenge does not claim that independent reproduction has already been achieved.

Independent reproduction is achieved only if a separate environment or third-party verifier completes the process, compares outputs against expected hashes, and publishes a completed independent reproduction report or attestation.

## Public References
- Repository: `EthicBit/EthicBit_CEMU`
- Public challenge release/tag: `aem-v1.1-independent-reproduction-challenge-2026-05-02`
- Prior registry publication tag: `aem-v1.1-global-registry-final-2026-05-01`
- Reproducibility Extension Anchor TX: `0x7c9651720faace92b6e66a739e1b5e176c202776bdf41ceea12e93386bcc196d`
- Reproducibility Extension Anchor Block: `25003750`

## Declared Subjects
This challenge is limited to four declared subjects:

- `global_public_verification_registry`: canonical JSON hash of the AEM V1.1 Global Public Verification Registry.
- `supply_chain_manifest`: canonical JSON hash of the Supply-Chain Verification Extension manifest.
- `slsa_provenance`: raw file SHA-256 of the published SLSA provenance artifact.
- `toolchain_fingerprint`: raw file SHA-256 of the published toolchain fingerprint.

These subjects test public registry integrity, supply-chain manifest integrity, provenance context, and toolchain context. They do not assert universal reproducibility for every repository output.

## Host Environment Boundary
The operator pre-send validation was performed on macOS and inside Docker Desktop. Docker mitigates most host-specific differences, but reviewers should record operating system, architecture, dependency versions, and any host-specific deviations in the environment fingerprint and reproduction report.

## Required Inputs
The independent reviewer should inspect:
- `assurance/reproducibility/declared_subjects.json`
- `assurance/reproducibility/expected_hashes.json`
- `docs/reproducibility/REPRODUCIBLE_BUILD_GUIDE.md`
- `receipts/AEM_V1_1_REPRODUCIBILITY_EXTENSION_MAINNET_ANCHOR_RECEIPT.json`

## Execution
Recommended command:

```bash
cd EthicBit_CEMU
source .venv/bin/activate 2>/dev/null || true
scripts/reproducibility/run_reproducibility_extension_e2e.sh
```

## Expected Result
The expected result is:

```text
REPRODUCIBILITY_EXTENSION_STATUS=PASS
REPRODUCIBILITY_COMPARISON_STATUS=PASS
subjects_total=4
subjects_matched=4
subjects_mismatched=0
current_closure=PUBLIC_REPRODUCIBLE_VERIFICATION_SUPPORT
target_closure=INDEPENDENTLY_REPRODUCED_RELEASE_BUILD
```

## Required Output From Reviewer
The reviewer should complete or produce:
- `assurance/reproducibility/independent_reproduction_report.json`
- `assurance/reproducibility/third_party_reproduction_attestation_template.json`
- comparison output;
- environment fingerprint;
- notes on machine, OS, dependency versions, and execution context.

## Claim Boundary
A successful independent run may support:

`INDEPENDENTLY_REPRODUCED_RELEASE_BUILD`

Only after the independent report and attestation are completed, reviewed, and accepted for the declared subjects.

Until then, the correct claim remains:

`PUBLIC_REPRODUCIBLE_VERIFICATION_SUPPORT`

## Supply-Chain Note
This challenge includes supply-chain context such as provenance, toolchain fingerprinting, manifests, signatures, and SBOM references where present. It does not claim SLSA L4 certification or universal supply-chain certification.
