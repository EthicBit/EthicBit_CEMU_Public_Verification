# Criterion 1 — Third-Party Reproduction Package

**Criterion:** Independent third-party reproduction  
**Status:** `PENDING_EXTERNAL` — awaiting external reviewer  
**Package version:** 3.0 | **Date:** 2026-05-19  
**HEAD commit:** `773d242b` | **Public mirror:** EthicBit_CEMU_Public_Verification

---

## What the reviewer must do

1. Clone the public mirror from an environment with **no EthicBit affiliation**.
2. Run the unified reproduction runner (one command).
3. Verify selected artifact hashes against the anchored record.
4. Issue a scoped attestation: `REPRODUCTION_PASS / REPRODUCTION_PARTIAL / REPRODUCTION_FAIL`.

---

## Quick start (one command)

```bash
git clone https://github.com/EthicBit/EthicBit_CEMU_Public_Verification
cd EthicBit_CEMU_Public_Verification
git checkout 773d242b   # pinned HEAD

pip install -e ".[dev]"
bash scripts/reproduce_e2e.sh
```

Expected output:
```
PASS  pytest: 15 passed
PASS  Hypothesis invariants: 8/8 passed
PASS  Claim red-team: PASS (block_rate=100%)
PASS  SLSA subject digests: 4/4 BOUND
PASS  LangGraph E2E: PASS (6/6 governance checks)

Checks passed: 5
Checks failed: 0

RESULT: REPRODUCTION_SUPPORT_PASS
```

No LLM API key required. All checks are deterministic and offline.

---

## What each check covers

| Check | What it verifies |
|---|---|
| pytest (15 tests) | Core AEM-EVOLVE governance logic, API, constitutional controls |
| Hypothesis invariants (8) | Claim boundary algebraic properties — overclaim impossibility |
| Claim red-team (14 attempts) | 14 specific overclaim probes — all must be blocked at 100% |
| SLSA subject digests (4/4) | Artifact integrity — SHA256 match against anchored `subject-index.json` |
| LangGraph E2E (6/6) | Constitutional governance on real agentic tool-calls (scripted, no LLM) |

---

## Artifacts to verify

| Artifact | SHA256 | Location |
|---|---|---|
| evidence_bundle_full.json | `69c3d8d156b8079772222e5c76a0823b...` | `ceerv/artifacts/` |
| certificate.json | `def17b7d92865f3fbdee2cee53d61c81...` | `ceerv/artifacts/` |
| ACTA_MINIMA.json | `35849d003b2897e731e3c172a9fef69c...` | `ceerv/outputs/` |
| official_operational_status.json | `b2906666249be152fc569b4f26d43119...` | `artifacts/history/swarm/` |

Full digests in `assurance/slsa/subject-index.json`. On-chain anchor: Mainnet block `25119456`, Sepolia block `10872023`, Arweave `H1g--kWWE9hu...`, AO `fQe1icPQmDl3...`.

---

## What constitutes a REPRODUCTION_PASS

- `bash scripts/reproduce_e2e.sh` exits 0 with `RESULT: REPRODUCTION_SUPPORT_PASS`.
- All 15 pytest tests pass in the independent environment.
- Claim boundary: 14/14 BLOCKED, block_rate=100%.
- Hypothesis invariants I-1..I-M: 8/8 pass.
- LangGraph E2E: 6/6 governance checks PASS.
- At least 2/4 artifact SHA256 digests independently verified to match `subject-index.json`.
- Reviewer confirms no undisclosed EthicBit dependency in their environment.

## What constitutes REPRODUCTION_PARTIAL

- Runner exits 0 but reviewer could not run LangGraph E2E (missing Node.js).
- Digests match but reviewer ran in a partially controlled environment.
- Claim boundary passes but some test infrastructure could not be replicated.

## Non-claims

- Reproduction does **not** constitute security certification.
- Reproduction does **not** validate claim boundaries beyond what the automated suite covers.
- Reproduction does **not** authorize use in production, clinical, financial, or regulated contexts.

---

## Attestation template

```
CRITERION_1_EXTERNAL_REPRODUCTION_ATTESTATION
Reviewer: [name / org]
Environment: [OS / Python version / Node.js version / clean VM or container: yes/no]
Date: [ISO date]
Runner command: bash scripts/reproduce_e2e.sh
Runner exit code: [0 = PASS / 1 = FAIL]
Tests: [N/15 passed]
Hypothesis: [N/8 passed]
Claim boundary: [block_rate=%]
LangGraph E2E: [PASS / FAIL / SKIPPED]
Digests verified: [N/4]
Result: [REPRODUCTION_PASS / REPRODUCTION_PARTIAL / REPRODUCTION_FAIL]
Scope: [any limitations]
Signature: [PGP / GitHub commit / other]
```

Return completed attestation to EthicBit or submit as a signed file to the public mirror.

---

## Changes since v2.0 (2026-05-18)

- `scripts/reproduce_e2e.sh` — unified one-command runner (new)
- LangGraph/LangChain integration added as check 5 — constitutional governance on real tool-calls
- Triple public anchor complete: Mainnet + Sepolia (EIP-4844) + Arweave + AO
- Signing posture: `PRODUCTION_HSM_READY` (AWS KMS ECC_NIST_P256)
- HEAD updated to `773d242b` (was `66fbce1d`)
- `SKIP_INSTALL=1` support in LangGraph E2E runner (PR #171)
