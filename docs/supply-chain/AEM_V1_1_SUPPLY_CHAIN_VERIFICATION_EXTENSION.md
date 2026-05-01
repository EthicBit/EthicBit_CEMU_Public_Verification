# AEM V1.1 Supply-Chain Verification Extension

Status: `PUBLIC_REPRODUCIBLE_VERIFICATION_SUPPORT`  
Scope: EthicBit/CEMU - AEM V1.1  
Effective Date: 2026-05-01  
Type: Supply-chain verification extension (no canonical mutation)

## 1. Purpose
This extension adds a public supply-chain verification layer to AEM V1.1 with:
- public SBOM artifacts;
- toolchain fingerprint capture;
- signed release verification bundle artifacts;
- signed provenance support artifacts;
- single-command release verification workflow.

## 2. Scope Boundary
This extension is additive and does not replace AEM V1.1 canonical governance artifacts.

## 3. Relationship to Canonical Artifacts
This extension does not modify the AEM V1.1 canonical artifact, the final Global Public Verification Registry, or the final Ethereum mainnet registry anchor. It adds a supply-chain verification layer for public reproducible verification support.

This extension preserves:
- canonical AEM V1.1 freeze integrity;
- global registry canonical hash integrity;
- final mainnet registry anchor receipt integrity.

## 4. Public Verification Subjects
Primary subjects are published under:
- `assurance/sbom/`
- `assurance/toolchain/`
- `assurance/provenance/`
- `assurance/release/`
- `assurance/signatures/`
- `receipts/AEM_V1_1_SUPPLY_CHAIN_VERIFICATION_EXTENSION_RECEIPT.json`

## 5. SBOM Artifacts
Two public SBOM formats are produced:
- `assurance/sbom/aem_v1_1_sbom.cyclonedx.json`
- `assurance/sbom/aem_v1_1_sbom.spdx.json`

These files support third-party package inventory and dependency review for release verification.

## 6. Toolchain Fingerprint
`assurance/toolchain/toolchain_fingerprint.json` captures:
- platform and runtime context;
- tool versions (git/python/node/npm/go/openssl/jq/docker when available);
- lockfile hashes and build input references.

## 7. Build Provenance
Provenance artifacts:
- `assurance/provenance/SLSA_PROVENANCE.json`
- `assurance/provenance/AEM_V1_1_BUILD_PROVENANCE.md`

These artifacts reference supply-chain subjects, source revision, and upstream registry/anchor linkage.

## 8. Signed Bundles and Reports
The extension signs its release verification manifest and publishes:
- `assurance/signatures/AEM_V1_1_SUPPLY_CHAIN_SIGNATURE_SET.json`
- `assurance/signatures/AEM_V1_1_SUPPLY_CHAIN_SIGNATURE_VERIFICATION.json`

## 9. Single-Command Verification Workflow
Third parties can verify the extension with:

```bash
bash scripts/verify_release.sh
```

This workflow validates:
- registry canonical hash alignment;
- final registry anchor receipt status;
- closure and constitutional snapshots;
- subject hash integrity;
- hybrid signature verification.

## 10. Current Claim Level
Approved claim:

`AEM V1.1 Supply-Chain Verification Extension provides public reproducible verification support through SBOM, signed provenance, toolchain fingerprinting, signed bundles, and a single-command release verification workflow.`

Not claimed:
- fully reproducible build;
- deterministic end-to-end rebuild;
- independent reproducible build proven;
- SLSA L4 fully achieved.

## 11. Limitations
The extension provides reproducible verification support over declared subjects and published evidence files. It does not assert external certification or third-party binding.

Boundary remains:
- `third_party_binding=false`
- `patent_grant_claimed=false`
- `uspto_approval_claimed=false`
- `regulatory_approval_claimed=false`
- `court_recognition_claimed=false`

## 12. Forward Path
Future releases may increase reproducibility claims only after declared-subject independent rebuild and deterministic hash comparison are demonstrated and receipted in a new extension layer.
