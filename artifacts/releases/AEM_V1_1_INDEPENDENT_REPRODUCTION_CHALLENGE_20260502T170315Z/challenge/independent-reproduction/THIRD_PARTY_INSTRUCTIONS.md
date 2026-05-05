# Third-Party Reviewer Instructions

## Scope
You are asked to independently verify declared AEM V1.1 reproducibility subjects using public repository materials.

This challenge is limited to declared subjects and expected hashes, and does not claim universal reproducibility.

## Step-by-Step
1. Clone repository:
```bash
git clone https://github.com/EthicBit/EthicBit_CEMU.git
cd EthicBit_CEMU
```
2. Checkout a declared public reference (tag/commit documented in challenge manifest).
3. Review:
   - `assurance/reproducibility/declared_subjects.json`
   - `assurance/reproducibility/expected_hashes.json`
   - `docs/reproducibility/REPRODUCIBLE_BUILD_GUIDE.md`
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

## Outcome Interpretation
- If declared subjects match expected hashes and your report is complete, your evidence may support advancement toward `INDEPENDENTLY_REPRODUCED_RELEASE_BUILD`.
- Until independent evidence is completed and reviewed, official closure remains `PUBLIC_REPRODUCIBLE_VERIFICATION_SUPPORT`.

