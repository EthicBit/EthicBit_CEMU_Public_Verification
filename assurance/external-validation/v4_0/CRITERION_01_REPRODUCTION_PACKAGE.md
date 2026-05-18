# Criterion 1 — Third-Party Reproduction Package

**Criterion:** Independent third-party reproduction  
**Status:** `PENDING_EXTERNAL` — awaiting external reviewer  
**Package version:** 2.0 | **Date:** 2026-05-18  
**HEAD commit:** `66fbce1d` | **Public mirror:** EthicBit_CEMU_Public_Verification

---

## What the reviewer must do

1. Clone the public mirror from an environment with **no EthicBit affiliation**.
2. Run the reproduction suite independently.
3. Verify selected artifact hashes against the anchored record.
4. Issue a scoped attestation: `REPRODUCTION_PASS / REPRODUCTION_PARTIAL / REPRODUCTION_FAIL`.

---

## Quick start

```bash
git clone https://github.com/EthicBit/EthicBit_CEMU_Public_Verification
cd EthicBit_CEMU_Public_Verification
git checkout 66fbce1d   # current HEAD

# Install dev deps
pip install -e ".[dev]"

# Run full test suite
pytest tests/ -q
# Expected: 15 passed

# Claim boundary red-team
python3 tools/external_validation/claim_red_team/run_claim_red_team.py --dry-run
# Expected: CLAIM_BOUNDARY_RED_TEAM=PASS, block_rate=100%

# Claim boundary Hypothesis property tests
pytest tests/test_claim_boundary_properties.py -v
# Expected: 8 passed (I-1..I-5, I-M, regression)

# Compute artifact digests (verify subject-index binding)
python3 scripts/slsa/compute_subject_digests.py
# Expected: 4/4 subjects BOUND — compare SHA256 against assurance/slsa/subject-index.json
```

---

## Artifacts to verify

| Artifact | SHA256 (current) | Location |
|----------|-----------------|----------|
| evidence_bundle_full.json | `69c3d8d156b8...` | `ceerv/artifacts/` |
| certificate.json | `def17b7d9286...` | `ceerv/artifacts/` |
| ACTA_MINIMA.json | `35849d003b28...` | `ceerv/outputs/` |
| official_operational_status.json | `b2906666249b...` | `artifacts/history/swarm/` |

Full digests in `assurance/slsa/subject-index.json`.

---

## What constitutes a REPRODUCTION_PASS

- All 15 tests pass in the independent environment.
- Claim boundary: 14/14 BLOCKED, block_rate=100%.
- Hypothesis invariants I-1..I-M: 8/8 pass.
- At least 2/4 artifact SHA256 digests independently verified to match `subject-index.json`.
- Reviewer confirms no undisclosed EthicBit dependency in their environment.

## What constitutes REPRODUCTION_PARTIAL

- Tests pass but reviewer was unable to run full Hypothesis suite.
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
Environment: [OS / Python version / clean VM or container: yes/no]
Date: [ISO date]
Tests: [N/15 passed]
Claim boundary: [block_rate=%]
Digests verified: [N/4]
Result: [REPRODUCTION_PASS / REPRODUCTION_PARTIAL / REPRODUCTION_FAIL]
Scope: [any limitations]
Signature: [PGP / GitHub commit / other]
```

Return completed attestation to EthicBit or submit as a signed file to the public mirror.

---

## New since 2026-05-14 (relevant to this criterion)

- `slsa-build.yml` active — build is now reproducible via CI (Block B3)
- `assurance/slsa/subject-index.json` — 4/4 digests bound (was TO_BE_BOUND stubs)
- `tests/test_claim_boundary_properties.py` — 8 Hypothesis property tests (Block C)
- `scripts/hooks/check_claim_consistency.py` — consistency gate now CI-enforced (Block E)
- Pre-commit hooks + PR gate (`pr-gate.yml`) — all pushes gated (Block E)
