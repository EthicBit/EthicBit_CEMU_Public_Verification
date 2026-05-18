# Framework Comparative Analysis — SLSA / in-toto / SSDF vs EthicBit/CEMU

**Version:** 1.0  
**Date:** 2026-05-18  
**Status:** ACTIVE  
**Scope:** EthicBit/CEMU v4.0 positioned against SLSA, in-toto, and NIST SSDF (SP 800-218)

---

## Overview

This document provides a structured technical comparison between EthicBit/CEMU and three
supply-chain / software assurance frameworks. The goal is to show:

1. Where EthicBit/CEMU implements each framework's requirements
2. Where it extends or diverges from them
3. What problems it solves that the frameworks do not address

---

## 1 — vs SLSA (Supply-chain Levels for Software Artifacts)

**Framework:** SLSA v1.0 — four tracks: Source, Build, Provenance, Common  
**Current EthicBit/CEMU SLSA status:** `BASELINE_DOCUMENTED` / `L4_ASPIRATIONAL` (not claimed L4)

| SLSA Requirement | SLSA Level | EthicBit/CEMU Implementation | Gap |
|---|---|---|---|
| Version controlled source | L1 | Git repository with protected main branch | None |
| Build service produces provenance | L1 | `slsa-build.yml` active; `assurance/slsa/build-manifest.json` per run | None |
| Provenance meets SLSA provenance spec | L2 | `assurance/slsa/l4/provenance.json` (SLSA provenance v1 buildType) | Builder ID references canonical workflow URI |
| Provenance authenticated with signing key | L3 | `slsa_hybrid_attest.yml` — hybrid Ed25519 + ML-DSA signing | Ed25519 required; ML-DSA conditional on risk mode |
| Hermetic build | L4 | `slsa-build.yml` — `npm ci --ignore-scripts`, locked deps | Hardhat compile conditional; not fully hermetic yet |
| Build definition in source (no params) | L4 | Build config in `package.json` (`build:hermetic` script); workflow declarative | Workflow allows `workflow_dispatch` — minor gap |
| in-toto attestation chain | L4 (aspirational) | 6-step chain (intake→closure), all KMS-signed | External witness pending |
| Subject index with SHA256 digests | L4 (aspirational) | `assurance/slsa/subject-index.json` — 4/4 subjects bound | `TO_BE_BOUND` eliminated; verified at 2026-05-18 |

**Where EthicBit/CEMU extends SLSA:**
- SLSA covers supply chain provenance for software artifacts. EthicBit/CEMU adds **claim boundary enforcement** (CBE) and **sector-aware constitutional controls** — SLSA has no analogue for AI output governance.
- SLSA does not address anchor receipts. EthicBit/CEMU adds Triple Public Anchor (Sepolia + Arweave + AO) + Mainnet KZG blob as tamper-evidence layer beyond git.
- SLSA does not define release class gates. EthicBit/CEMU `anchor-policy.json` defines DEVELOPMENT / CONTROLLED_EVIDENCE / EXTERNAL_VALIDATION / PRODUCTION_RELEASE with per-class prerequisites.

**Where SLSA is ahead of current EthicBit/CEMU:**
- SLSA defines a formal builder identity model with OIDC tokens. EthicBit/CEMU uses KMS-based signing (strong) but without OIDC-anchored builder identity.
- SLSA L4 full hermetic build is not yet achieved; current posture is `BASELINE_DOCUMENTED`.

---

## 2 — vs in-toto

**Framework:** in-toto v1.0 — supply chain integrity via link metadata, layouts, and functionary identities  
**Current EthicBit/CEMU in-toto status:** `KMS_SIGNED_PENDING_EXTERNAL_WITNESS`

| in-toto Requirement | EthicBit/CEMU Implementation | Gap |
|---|---|---|
| Layout defining steps and functionaries | `assurance/in-toto/` schema directory; 6-step layout (intake, provenance, governance, fixation, sealing, closure) | Formal in-toto layout.json not yet a machine-executable layout spec |
| Link metadata per step | Each statement JSON is a step attestation with subject, step name, and signer | Not in canonical in-toto link envelope format (uses custom ETHICBIT_IN_TOTO_STATEMENT_V1) |
| Functionary signing key | KMS key `alias/ethicbit-intoto-signing` (ECC_NIST_P256); ARN embedded in `signedBy` | KMS-backed (strong) vs software key; in-toto spec supports any asymmetric key |
| Signature verification | ECDSA_SHA_256 over SHA256(canonical_payload); `payloadSHA256` recorded | Verification requires AWS KMS Verify API or public key export |
| External witness / threshold signatures | Not yet implemented | `KMS_SIGNED_PENDING_EXTERNAL_WITNESS` — this is the primary open gap |
| Transport: DSSE or JWS envelope | Custom JSON envelope (not DSSE) | Full in-toto v1 DSSE compliance not implemented |

**Where EthicBit/CEMU extends in-toto:**
- in-toto is supply-chain-only. EthicBit/CEMU adds **constitutional controls per sector**, **claim boundary enforcement**, and **anchor receipts** that go beyond what in-toto defines.
- in-toto does not define claim governance. EthicBit/CEMU's CBE prevents semantic overclaims from propagating even when the technical chain is intact.
- in-toto does not define release class escalation gates. EthicBit/CEMU requires `KMS_SIGNED` before `EXTERNAL_VALIDATION` anchor class and `EXTERNALLY_WITNESSED` before `PRODUCTION_RELEASE`.

**Where in-toto is ahead:**
- Full DSSE transport envelope compliance.
- Machine-executable layout policy (in-toto-run, in-toto-verify).
- Multi-party threshold signing via functionary key sets.

---

## 3 — vs SSDF (NIST SP 800-218)

**Framework:** NIST Secure Software Development Framework, v1.1 (February 2022)  
**Practices:** PO (Prepare Org), PS (Protect Software), PW (Produce Well-Secured Software), RV (Respond to Vulnerabilities)

| SSDF Practice | EthicBit/CEMU Implementation | Status |
|---|---|---|
| **PO.1** — Define security requirements | Constitutional controls, sector-aware ME gates; `level4-policy.json` requirements list | ADDRESSED |
| **PO.2** — Implement a risk-based approach | STRIDE/LINDDUN/ATLAS threat model; risk_modes (STANDARD/HIGH/GOV) in SLSA policy | ADDRESSED |
| **PO.3** — Implement supporting toolchains | KMS signing scripts (`sign_intoto_statements_kms.py`, `sign_sbom_kms.py`); SLSA build scripts (`compute_subject_digests.py`, `generate_build_manifest.py`) | ADDRESSED |
| **PO.5** — Implement and maintain secure environments | GitHub Actions with minimal permissions; KMS IAM least-privilege; `.gitignore` excludes secrets | ADDRESSED |
| **PS.1** — Store all forms of code securely | Git with protected branches; KMS-signed provenance; anchor receipts for tamper evidence | ADDRESSED |
| **PS.2** — Provide a mechanism for code review | Pull request workflow; external validation package for independent review (criteria 1, 2, 8) | PARTIAL — no required PR reviewer count enforced |
| **PS.3** — Archive and protect each software release | `assurance/release/`; anchor receipts (immutable on-chain); CEERV FORMALLY_FROZEN | ADDRESSED |
| **PW.1** — Design software to meet security requirements | Fail-closed constitutional gates; PROHIBITED_AUTOMATED_ELEVATIONS; CBE blocking | ADDRESSED |
| **PW.4** — Reuse existing, well-secured software | CycloneDX SBOM (654 components); `npm ci` with lockfile; pip with lockfile | ADDRESSED |
| **PW.5** — Create source code by adhering to secure coding practices | Ruff linter in dev dependencies; mypy type checking; `--ignore-scripts` on npm | PARTIAL — no pre-commit hooks yet (Block E) |
| **PW.6** — Configure the compilation, interpreter, and build processes securely | `slsa-build.yml` uses `persist-credentials: false`; `--no-build-isolation` for pip | ADDRESSED |
| **PW.7** — Review and test code to identify vulnerabilities | Hypothesis property tests (500 examples); red-team 14 cases; RuntimeGuard L4 negative tests | ADDRESSED |
| **PW.8** — Perform root cause analysis of vulnerabilities | External audit 4/10 findings → root cause documented → Block A-E remediation plan | ADDRESSED |
| **RV.1** — Identify and confirm vulnerabilities | External audit findings C1-C3, A1-A5, M1-M4 identified and triaged | ADDRESSED |
| **RV.2** — Assess, prioritize, and remediate vulnerabilities | A-block this week, B+C next month, D+E following month; sequence documented in remediation plan | ADDRESSED |
| **RV.3** — Analyze vulnerabilities for root causes | Block A closed SLSA contradiction (C1); Block B2 closed unsigned in-toto (C2); Block B3 closed missing build workflow (C3) | ADDRESSED |

**Where EthicBit/CEMU extends SSDF:**
- SSDF is software-development-focused and does not address AI-specific output governance, sector-aware ethics enforcement, or claim boundary management.
- SSDF does not define blockchain/anchor-based tamper evidence — EthicBit/CEMU adds this as a layer above what SSDF requires.
- SSDF does not define release classes with escalating prerequisites — EthicBit/CEMU's anchor-policy.json formalizes this.

**Remaining SSDF gaps:**
- Pre-commit hooks (Block E) — PW.5 partial
- Required PR reviewer enforcement (GitHub branch protection) — PS.2 partial
- Formal vulnerability disclosure policy — RV.3 partial (no public bug bounty or CVE process defined)

---

## 4 — Summary Positioning

| Dimension | SLSA | in-toto | SSDF | EthicBit/CEMU |
|-----------|------|---------|------|---------------|
| Supply chain provenance | ✓ Core | ✓ Core | Partial | ✓ Implemented (BASELINE_DOCUMENTED) |
| Artifact signing (KMS) | Optional | Optional | Recommended | ✓ Mandatory (B2-B4 complete) |
| Hermetic build | L4 required | Out of scope | PO.3/PW.6 | Partial (slsa-build.yml, not fully hermetic) |
| Claim boundary enforcement | ✗ | ✗ | ✗ | ✓ Core (14-case CBE, Hypothesis tests) |
| AI sector-aware ethics gates | ✗ | ✗ | ✗ | ✓ Core (7 sectors, constitutional controls) |
| On-chain tamper evidence | ✗ | ✗ | ✗ | ✓ Triple Public Anchor + Mainnet KZG |
| External witness / threshold sig | L4 spec | ✓ Spec | ✗ | Pending (KMS_SIGNED_PENDING_EXTERNAL_WITNESS) |
| Formal conformance certification | Via SLSA verifier | Via in-toto-verify | Via SSDF assessment | Not claimed — BASELINE_DOCUMENTED |
| AI RMF / ISO 42001 alignment | ✗ | ✗ | Partial | ✓ Mapped (see companion documents) |

---

*This analysis is informational. It reflects EthicBit/CEMU v4.0 as of 2026-05-18. No certification to SLSA, in-toto, or SSDF conformance is claimed.*
