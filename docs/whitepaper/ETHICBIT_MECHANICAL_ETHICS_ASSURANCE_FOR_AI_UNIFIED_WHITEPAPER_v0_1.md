# EthicBit Mechanical Ethics Assurance for AI

## Unified Public-Verifiable Assurance Snapshot v0.1

**Prepared by:** EthicBit / CEMU  
**Publication series:** EthicBit/CEMU Public Verification Series  
**Date:** May 2026  
**Repository:** `EthicBit/EthicBit_CEMU`  
**Unified manifest:** `assurance/unified/ETHICBIT_MECHANICAL_ETHICS_ASSURANCE_UNIFIED_MANIFEST_v0_1.json`  
**Unified anchor receipt:** `assurance/unified/ETHICBIT_MECHANICAL_ETHICS_ASSURANCE_UNIFIED_ANCHOR_RECEIPT_v0_1.json`

---

## 1. Executive Summary

EthicBit Mechanical Ethics Assurance for AI consolidates the current EthicBit/CEMU assurance stack into a GitHub-inspectable, scope-delimited, public-verifiable architecture.

The unified manifest v0.1 is the official snapshot of the current assurance stack. It references artifact assurance, governed evolution assurance, public evidence surfaces, Ethereum mainnet integrity anchors, SLSA-style supply-chain assurance, ML-KEM768 + X25519 runtime secret protection, and explicit claim boundaries.

The unified manifest is now anchored on Ethereum mainnet as a public timestamped integrity reference.

**Current public claim:** `PUBLIC_REPRODUCIBLE_VERIFICATION_SUPPORT`

This does not claim regulatory approval, clinical validation, diagnostic authorization, production readiness, lab readiness, full SLSA L4 certification, FIPS module validation, absolute quantum security, completed independent reproduction, or automatic third-party binding.

---

## 2. Canonical Unified Anchor

| Field | Value |
|---|---|
| Status | `ONCHAIN_UNIFIED_MECHANICAL_ETHICS_ASSURANCE_ANCHOR_VERIFIED` |
| Network | `ethereum-mainnet` |
| Chain ID | `1` |
| TX | `0x4053d1102cf3368af730b58cc87debacd69c14613d5add6a7844a116a4b5e04d` |
| Block | `25037049` |
| Fee paid | `0.0008966558360376 ETH` |
| Manifest canonical SHA-256 | `cb5317a9c947ee5b438d2a280643d5ccbc924dea45ee2ca4c65fda8b1b56b14e` |
| Manifest file SHA-256 | `673d2c72fe31d466e350022d3fd74fb366138c83937eefb67e490dbab31aa89e` |
| Manifest canonicalization | `json_sort_keys_no_whitespace_utf8` |
| Payload SHA-256 | `2e1759e7c43b9125fb97f61098898b8b3d8f99b80a69e22d7fcbdc389e3065f7` |
| Main merge commit | `444075edb5a172056dd241364abeb28f5a86838e` |
| Generation base commit | `cdc3e377d70f660c55a89db9a4bcaa4e4034f8d3` |

Etherscan reference:

`https://etherscan.io/tx/0x4053d1102cf3368af730b58cc87debacd69c14613d5add6a7844a116a4b5e04d`

---

## 3. Assurance Stack Hierarchy

### Layer 1 - Artifact Assurance

AEM V1.1 verifies the artifact.

Primary evidence includes the AEM V1.1 public registry, canonical registry hash, and final Ethereum mainnet registry anchor.

### Layer 2 - Governed Evolution Assurance

AEM-EVOLVE governs the change.

Primary evidence includes the AEM-EVOLVE concept paper, technical demonstration manifest, signed evolution receipt verification, and AEM-EVOLVE mainnet anchor receipt.

### Layer 3 - Public Evidence Surface

GitHub exposes the evidence.

Primary evidence includes the public repository, release tags, reproducibility challenge pack, manifests, receipts, scripts, and verification reports.

### Layer 4 - Integrity Anchoring

Ethereum mainnet anchors the integrity.

Primary evidence includes anchors for the AEM V1.1 registry, supply-chain verification extension, reproducibility extension, AEM-EVOLVE technical demonstration, and this unified assurance manifest.

### Layer 5 - Supply-Chain Assurance

SLSA-style posture supports supply-chain assurance.

Primary evidence includes SBOM artifacts, SLSA-style provenance, in-toto style attestation references, signed release materials, release verification scripts, and executable baseline checks.

### Layer 6 - Runtime Secret Protection

ML-KEM768 + X25519 protects runtime secrets.

Primary evidence includes the runtime secret protection posture, hybrid ML-KEM768 + X25519 flow, HKDF-derived hybrid secret posture, fail-closed behavior, and non-sensitive metadata recording.

### Layer 7 - Scope Boundary Layer

Scope boundaries prevent overclaiming.

Primary evidence includes legal and third-party representation boundaries, AEM-EVOLVE scope boundaries, runtime secret protection non-claims, and public claim limitations.

---

## 4. What Is Verified Now

| Area | Current evidence | Verified posture |
|---|---|---|
| AEM V1.1 artifact | Registry, canonical hash, receipt, mainnet anchor | Artifact assurance is public-verifiable and anchored |
| AEM-EVOLVE | Concept paper, controlled technical demo, signed receipt verification, anchor | Governed change assurance is technically demonstrated and anchored |
| Public evidence | GitHub repository, releases, tags, challenge packs | Evidence surface is inspectable and reproducibility-oriented |
| Integrity anchoring | Ethereum mainnet receipts | Integrity references are timestamped on-chain |
| Supply chain | SBOM/provenance-oriented artifacts, SLSA-style posture, in-toto style artifacts, release verification | Supports public release verification; full SLSA L4 achievement is not claimed |
| Runtime secret protection | ML-KEM768 + X25519 posture and test coverage | Hybrid runtime secret protection posture is documented; FIPS module validation is not claimed |
| Scope boundary | Legal, technical, crypto, regulatory, and third-party non-claims | Overclaiming boundaries are explicit |

---

## 5. Upstream Anchors Referenced by the Unified Manifest

| Subject | Status | TX | Block |
|---|---|---|---|
| AEM V1.1 Global Registry | `ONCHAIN_REGISTRY_ANCHOR_VERIFIED` | `0xa2040997b6cccd182b5cf76daa23558540ab7be566f2e1c7527abcadbd5dddb4` | `25001458` |
| AEM V1.1 Supply-Chain Verification Extension | `ONCHAIN_SUPPLY_CHAIN_EXTENSION_ANCHOR_VERIFIED` | `0x2c9befb0398d90aee0c831837664c9c883700497ebb81fe7a7d9acf3b1d58fef` | `25002628` |
| AEM V1.1 Reproducibility Extension | `ONCHAIN_REPRODUCIBILITY_EXTENSION_ANCHOR_VERIFIED` | `0x7c9651720faace92b6e66a739e1b5e176c202776bdf41ceea12e93386bcc196d` | `25003750` |
| AEM-EVOLVE Technical Demonstration | `ONCHAIN_AEM_EVOLVE_TECHNICAL_DEMONSTRATION_ANCHOR_VERIFIED` | `0xaa23162993569913d557c98bc98703ffd716670551d9911c0d232dc8e860e40c` | `25032920` |
| Unified Mechanical Ethics Assurance Manifest v0.1 | `ONCHAIN_UNIFIED_MECHANICAL_ETHICS_ASSURANCE_ANCHOR_VERIFIED` | `0x4053d1102cf3368af730b58cc87debacd69c14613d5add6a7844a116a4b5e04d` | `25037049` |

---

## 6. How to Verify

A reviewer may inspect the unified manifest and receipt directly in the repository:

```bash
cat assurance/unified/ETHICBIT_MECHANICAL_ETHICS_ASSURANCE_UNIFIED_MANIFEST_v0_1.json
cat assurance/unified/ETHICBIT_MECHANICAL_ETHICS_ASSURANCE_UNIFIED_ANCHOR_RECEIPT_v0_1.json
```

A reviewer may recompute the canonical manifest hash using deterministic JSON canonicalization:

```bash
python3 - <<'PY'
import hashlib, json
from pathlib import Path
p = Path('assurance/unified/ETHICBIT_MECHANICAL_ETHICS_ASSURANCE_UNIFIED_MANIFEST_v0_1.json')
obj = json.loads(p.read_text(encoding='utf-8'))
canonical = json.dumps(obj, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode('utf-8')
print(hashlib.sha256(canonical).hexdigest())
PY
```

Expected canonical SHA-256:

```text
cb5317a9c947ee5b438d2a280643d5ccbc924dea45ee2ca4c65fda8b1b56b14e
```

A reviewer may also check the receipt TX on Ethereum mainnet:

```text
https://etherscan.io/tx/0x4053d1102cf3368af730b58cc87debacd69c14613d5add6a7844a116a4b5e04d
```

---

## 7. Current Public Claims

EthicBit/CEMU currently supports the following public claim:

```text
PUBLIC_REPRODUCIBLE_VERIFICATION_SUPPORT
```

The correct public formulation is:

EthicBit Mechanical Ethics Assurance Unified Manifest v0.1 is the official public-verifiable snapshot of the current EthicBit/CEMU assurance stack. It is GitHub-inspectable, scope-delimited, and anchored on Ethereum mainnet as a public timestamped integrity reference.

---

## 8. Claims Not Made

This whitepaper, manifest, receipt, and architecture do not claim:

- regulatory approval;
- clinical validation;
- diagnostic authorization;
- medical device approval;
- production readiness;
- lab readiness;
- full SLSA L4 certification;
- SLSA L4 fully achieved status;
- universal reproducibility;
- full offline hermetic reproducibility;
- FIPS module validation;
- cryptographic module certification;
- absolute quantum security;
- third-party cryptographic certification;
- completed independent release reproduction;
- automatic third-party binding;
- FDA or EMA acceptance;
- GxP certification;
- CE marking;
- guaranteed safety.

---

## 9. Strategic Interpretation

EthicBit turns AI governance into verifiable assurance.

AEM V1.1 verifies the artifact.  
AEM-EVOLVE governs the change.  
GitHub exposes the evidence.  
Ethereum mainnet anchors the integrity.  
SLSA-style provenance supports the supply chain.  
ML-KEM768 hybrid protection secures runtime secrets.  
Scope boundaries prevent overclaiming.

---

## 10. Conclusion

The unified manifest v0.1 provides a single public-verifiable snapshot of the current EthicBit/CEMU Mechanical Ethics Assurance stack.

The Ethereum mainnet anchor does not create regulatory, clinical, cryptographic, or third-party certification. It provides a public timestamped integrity reference for the declared manifest hash and its scope-delimited assurance posture.

**EthicBit Mechanical Ethics Assurance for AI** - public-verifiable, scope-delimited, GitHub-inspectable, and anchored on Ethereum mainnet.
