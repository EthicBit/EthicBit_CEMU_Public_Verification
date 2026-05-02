# Third-Party Reviewer Instructions

## Scope
You are asked to independently verify declared AEM V1.1 reproducibility subjects using public repository materials.

This challenge is limited to declared subjects and expected hashes, and does not claim universal reproducibility.

## Host Environment Note
The operator pre-send validation was performed on macOS and also inside Docker Desktop. External reviewers may use Linux, macOS, or another clean environment.

Docker is recommended because it reduces host-specific differences. Any host-specific deviation should be recorded in the environment fingerprint and reviewer notes.

## Declared Subjects
The reproduction scope is limited to four declared subjects:

- `global_public_verification_registry`: canonical JSON hash of the AEM V1.1 Global Public Verification Registry.
- `supply_chain_manifest`: canonical JSON hash of the Supply-Chain Verification Extension manifest.
- `slsa_provenance`: raw file SHA-256 of the published SLSA provenance artifact.
- `toolchain_fingerprint`: raw file SHA-256 of the published toolchain fingerprint.

These subjects were selected to cover public registry integrity, supply-chain manifest integrity, provenance context, and toolchain context. They do not claim universal reproducibility for every repository output.

## Step-by-Step
1. Verify ZIP integrity against the sibling `.sha256` file if using the challenge pack ZIP.

1. Clone repository:
```bash
git clone https://github.com/EthicBit/EthicBit_CEMU.git
cd EthicBit_CEMU
```
2. Checkout the declared public challenge reference:
```bash
git checkout aem-v1.1-independent-reproduction-challenge-2026-05-02
```

3. Review:
   - `assurance/reproducibility/declared_subjects.json`
   - `assurance/reproducibility/expected_hashes.json`
   - `docs/reproducibility/REPRODUCIBLE_BUILD_GUIDE.md`
   - `receipts/AEM_V1_1_REPRODUCIBILITY_EXTENSION_MAINNET_ANCHOR_RECEIPT.json`

4. Execute:
```bash
source .venv/bin/activate 2>/dev/null || true
scripts/reproducibility/run_reproducibility_extension_e2e.sh
```
5. Capture generated artifacts:
   - `assurance/reproducibility/comparison_report.json`
   - `assurance/reproducibility/environment_fingerprint.json`
6. Complete:
   - `assurance/reproducibility/independent_reproduction_report.json`
   - `assurance/reproducibility/third_party_reproduction_attestation_template.json`

## Optional Additional Review
Reviewers may optionally perform a more independent rebuild or regeneration of declared subjects and compare observed hashes against official expected hashes.

SLSA provenance and in-toto style attestations are not claimed as SLSA L4 certification in this challenge. They may be expanded in future supply-chain assurance work.

## Outcome Interpretation
- If declared subjects match expected hashes and your report is complete, your evidence may support advancement toward `INDEPENDENTLY_REPRODUCED_RELEASE_BUILD`.
- The closure should only be marked as `INDEPENDENTLY_REPRODUCED_RELEASE_BUILD` after the independent report and attestation are completed, reviewed, and accepted for the declared subjects.
- Until independent evidence is completed and reviewed, official closure remains `PUBLIC_REPRODUCIBLE_VERIFICATION_SUPPORT`.
