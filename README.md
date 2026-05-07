# EthicBit/CEMU Public Verification Mirror

This repository is the public verification mirror for **EthicBit Mechanical Ethics Assurance for AI**.

It contains public verification materials, whitepapers, manifests, receipts, registry artifacts, anchor references, reproducibility materials, SBOM/provenance artifacts, and minimal verification scripts.

This repository is **not** the full engineering repository. It is a sanitized public evidence mirror intended to support inspection of the claims made in the EthicBit public landing page and Unified Stack v0.1 release.

## Scope

GitHub-inspectable / Public-verifiable / Ethereum-mainnet anchored / Scope-delimited / Not yet independently reproduced.

## Current Public Claim

`PUBLIC_REPRODUCIBLE_VERIFICATION_SUPPORT`

## Unified Anchor

- Status: `ONCHAIN_UNIFIED_MECHANICAL_ETHICS_ASSURANCE_ANCHOR_VERIFIED`
- Network: `ethereum-mainnet`
- TX: `0x4053d1102cf3368af730b58cc87debacd69c14613d5add6a7844a116a4b5e04d`
- Block: `25037049`
- Manifest canonical SHA-256: `cb5317a9c947ee5b438d2a280643d5ccbc924dea45ee2ca4c65fda8b1b56b14e`

## Verification

```bash
bash scripts/verify_release.sh
bash scripts/evolve/run_evolve_demo.sh
bash scripts/reproducibility/run_reproducibility_extension_e2e.sh
```

## Non-Claims

This repository does not claim regulatory approval, clinical validation, production readiness, full SLSA L4, FIPS validation, independent reproduction, or automatic third-party binding.
