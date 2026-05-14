# EthicBit/CEMU Public Verification Mirror

This repository is the public verification mirror for **EthicBit Mechanical Ethics Assurance for AI**.

It contains public verification materials, whitepapers, manifests, receipts, registry artifacts, anchor references, reproducibility materials, SBOM/provenance artifacts, controlled evidence reports, and minimal verification scripts.

This repository is **not** the full engineering repository. It is a sanitized public evidence mirror intended to support inspection of public EthicBit/CEMU claims.

## Current Public Verification State

| Layer | Public status | Evidence |
|---|---:|---|
| Unified Stack v0.1 | Ethereum-mainnet anchored | `assurance/unified/` |
| AEM V1.1 Artifact Assurance | Public-verifiable / anchored | `registry/`, `receipts/` |
| AEM-EVOLVE v2.0 | `PASS` for `staging_controlled_cloud` | `assurance/evolve-multi-agent/v2_0/` |
| AEM-EVOLVE v3.0 | Category and doctrine release | `docs/releases/`, `docs/whitepapers/` |
| AI-ME v3.1 | `EVIDENCE_PASS`, 12/12 gates | `assurance/ai-me/v3_1/` |
| Fast Path v1.0 | `EVIDENCE_PASS`, 9/9 scenarios | `assurance/fast-path/v1/` |
| v4.0 external validation path | `CONTROLLED_EVIDENCE_PARTIAL`, 3/8 controlled pass, 5/8 pending external | `assurance/v4_0/`, `docs/external-validation/` |

## Current Public Claim

EthicBit has advanced from a v2.0 controlled infrastructure assurance baseline into AEM-EVOLVE v3.1 AI-Specific Mechanical Ethics evidence and v4.0 controlled external-validation preparation.

## Unified Anchor

- Status: `ONCHAIN_UNIFIED_MECHANICAL_ETHICS_ASSURANCE_ANCHOR_VERIFIED`
- Network: `ethereum-mainnet`
- TX: `0x4053d1102cf3368af730b58cc87debacd69c14613d5add6a7844a116a4b5e04d`
- Block: `25037049`
- Manifest canonical SHA-256: `cb5317a9c947ee5b438d2a280643d5ccbc924dea45ee2ca4c65fda8b1b56b14e`

## Additional Public Anchors

- AEM-EVOLVE Multi-Agent API demo anchor: `0x30fc9e6c810078c42ac1b840c3712d165342436ec427471b7f955425ea4b8275`
- AEM-EVOLVE financial/cyber execution demo anchor: `0x5067b7c194eed0578f22d54332c6eb9620bb7aee5d2421fe257116a88e3f7091`

## Key Status Documents

- `docs/STATUS_BULLETIN_PUBLIC_2026-05-12_V3_0.md`
- `docs/STATUS_BULLETIN_PUBLIC_2026-05-12_V3_1_EVIDENCE.md`
- `docs/STATUS_BULLETIN_PUBLIC_2026-05-12_FAST_PATH_V1_0_EVIDENCE.md`
- `docs/STATUS_BULLETIN_PUBLIC_2026-05-12_V4_0_CONTROLLED_EVIDENCE.md`
- `docs/technology/ETHICBIT_FULL_TECHNOLOGY_STATE_V3_0.md`

## Verification

```bash
bash scripts/verify_release.sh
bash scripts/evolve/run_evolve_demo.sh
bash scripts/reproducibility/run_reproducibility_extension_e2e.sh
```

Additional controlled evidence can be inspected through the JSON reports under `assurance/`.

## Non-Claims

This repository does not claim completed third-party reproduction, external certification, regulatory approval, universal production readiness, clinical or diagnostic readiness, cybersecurity certification, financial advice, full SLSA L4 certification, FIPS validation, HSM-backed custody unless separately evidenced, or automatic third-party binding.

v4.0 is **not** claimed complete. The current v4.0 state is `CONTROLLED_EVIDENCE_PARTIAL` with 3/8 controlled criteria and 5/8 criteria pending external validation.
