# Third-Party Reproduction Kit v4.0

**Document type:** Reproduction Kit  
**Version:** 4.0 (Ready)  
**Status:** `ACTIVE — all 8 v4.0 criteria executed — 3 CONTROLLED_PASS — 5 PENDING_EXTERNAL — Ethereum mainnet anchor confirmed`  
**Constitutional dependency:** EthicBit / CEMU v3.7.0+  
**Date:** 2026-05-14  
**Release:** `aem-evolve-v4.0-controlled-evidence-2026-05-14`

---

## Overview

This kit enables independent third parties to reproduce EthicBit AEM-EVOLVE v4.0 evidence in an independent environment.

**Current state:** All 8 v4.0 acceptance criteria have been executed. AI-ME v3.1 is EVIDENCE_PASS (12/12 gates). Fast Path v1.0 is EVIDENCE_PASS (9/9 scenarios). Criteria 5, 6, and 7 are CONTROLLED_PASS. Criteria 1, 2, 3, 4, and 8 are PENDING_EXTERNAL — each has a controlled assessment artifact and is ready for external engagement. Ethereum mainnet anchor confirmed at block 25095358.

---

## Quickstart

### Requirements

- Docker or Colima (local) OR managed cloud environment
- Python 3.11+
- PostgreSQL (managed or local)
- Access to the EthicBit AEM-EVOLVE repository

### Setup

```bash
# Clone the repository
git clone <repository-url>
cd EthicBit_CEMU

# Set up Python environment
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Set up environment variables
cp .env.template .env.local
# Edit .env.local with your environment values

# Start services
docker-compose up -d  # or equivalent managed cloud setup
```

### Run AI-ME v3.1 evidence (full 12-gate execution)

```bash
# Run all 12 AI-ME gates and produce aggregate report
python3 demos/aem-evolve-multi-agent-api/tools/ai_me/run_ai_me_evidence_v3_1.py
# Expected: PASS 12/12 gates, artifact_verified=true all gates
# Output: assurance/ai-me/v3_1/AI_ME_V3_1_AGGREGATE_REPORT.json

# Run Fast Path v1.0 evidence (9 scenarios)
python3 demos/aem-evolve-multi-agent-api/tools/fast_path/run_fast_path_evidence_v1_0.py
# Expected: EVIDENCE_PASS 9/9 scenarios, 7/7 mandatory rules verified
# Output: assurance/fast-path/v1/FAST_PATH_VERIFICATION_REPORT.json

# Verify v4.0 criterion artifacts (all 8 present and populated)
ls assurance/v4_0/evidence/
# Expected: 8 artifact files — V4_0_01 through V4_0_08

# Verify v4.0 evidence report
python3 -c "
import json
r = json.load(open('assurance/v4_0/V4_0_CONTROLLED_EVIDENCE_REPORT.json'))
print(r.get('controlled_evidence_status', r.get('status')))
"
# Expected: 3 CONTROLLED_PASS, 5 PENDING_EXTERNAL
```

---

## Expected Evidence Outputs

Each AI-ME gate produces a JSON report at:
```
assurance/ai-me/v3_1/AI-ME-0X_report.json
```

Expected acceptance criteria per gate are defined in:
```
docs/ai-me/AI_ME_GATE_MATRIX_V3_1.json
```

Expected outcomes by artifact type:

| Artifact | Expected outcome | Path |
|---|---|---|
| AI-ME v3.1 aggregate | `PASS 12/12` | `assurance/ai-me/v3_1/AI_ME_V3_1_AGGREGATE_REPORT.json` |
| Fast Path verification | `EVIDENCE_PASS 9/9` | `assurance/fast-path/v1/FAST_PATH_VERIFICATION_REPORT.json` |
| v4.0 controlled evidence report | `3 CONTROLLED_PASS, 5 PENDING_EXTERNAL` | `assurance/v4_0/V4_0_CONTROLLED_EVIDENCE_REPORT.json` |
| v4.0 criterion artifacts | 8 files — see table below | `assurance/v4_0/evidence/` |

### v4.0 criterion artifacts

| # | Artifact | Controlled Status |
|---|---|---|
| 1 | V4_0_01_REPRODUCTION_KIT_ARTIFACT.json | PENDING_EXTERNAL (CONTROLLED_SELF_REPRODUCTION_PASS) |
| 2 | V4_0_02_SECURITY_REVIEW_ARTIFACT.json | PENDING_EXTERNAL (CONTROLLED_ASSESSMENT_PASS_INTERNAL_CONTROLS) |
| 3 | V4_0_03_CLOUD_DEPLOYMENT_ARTIFACT.json | PENDING_EXTERNAL (CONTROLLED_ASSESSMENT_PASS_DOCUMENTATION_AND_CODE_TIER) |
| 4 | V4_0_04_HSM_SIGNING_ARTIFACT.json | PENDING_EXTERNAL (CONTROLLED_ASSESSMENT_PASS_SOFTWARE_SIGNING_CODE_TIER) |
| 5 | V4_0_05_AEM_REVERIFICATION_ARTIFACT.json | CONTROLLED_PASS |
| 6 | V4_0_06_TRIPLE_ANCHOR_ARTIFACT.json | CONTROLLED_PASS |
| 7 | V4_0_07_FAST_PATH_BENCHMARK_ARTIFACT.json | CONTROLLED_PASS |
| 8 | V4_0_08_CLAIM_REVIEW_ARTIFACT.json | PENDING_EXTERNAL (CONTROLLED_CLAIM_AUDIT_PASS) |

---

## Hash Verification Instructions (AEM v1.1)

For each AI-ME v3.1 evidence artifact:

```bash
# Compute SHA-256 hash
sha256sum assurance/ai-me/v3_1/evidence/AI_ME_0X_*.json

# Compare against declared hash in AEM v1.1 receipt
python3 -c "
import json, hashlib
with open('assurance/ai-me/v3_1/receipt_AI-ME-01_model_evaluation_artifact.json') as f:
    receipt = json.load(f)
declared = receipt['artifact_hash']
with open(receipt['artifact_path'], 'rb') as f:
    computed = hashlib.sha256(f.read()).hexdigest()
print(f'PASS' if declared == computed else f'FAIL: declared={declared} computed={computed}')
"
```

Repeat for all 12 AI-ME v3.1 receipts in `assurance/ai-me/v3_1/receipt_AI-ME-*.json`.

---

## AEM v1.1 Artifact Verification Checklist

- [ ] All required artifacts listed in `AI_ME_GATE_MATRIX_V3_1.json` are present
- [ ] SHA-256 hash of each artifact matches declared hash in AEM v1.1 manifest
- [ ] Verification receipts exist for each verified artifact
- [ ] Public anchor references verified where anchor receipts exist

---

## Triple Anchor Verification Checklist

- [ ] Verify Sepolia anchor (v3.1+FastPath): `assurance/v4_0/V4_0_SEPOLIA_ANCHOR_RECEIPT.json` — block 10840044
- [ ] Verify Sepolia anchor (v4.0 all criteria): `assurance/v4_0/V4_0_CONTROLLED_EVIDENCE_ANCHOR_RECEIPT.json` — block 10852797
- [ ] Verify Mainnet anchor (v4.0): `assurance/v4_0/V4_0_MAINNET_ANCHOR_RECEIPT.json` — block 25095358
- [ ] Confirm `status: "ONCHAIN_BLOB_ANCHOR_VERIFIED"` in each receipt
- [ ] Confirm criterion artifact hashes in mainnet receipt match local files via SHA-256
- [ ] Mainnet TX explorer: https://etherscan.io/tx/0xd5fe44459f15e1cb3230f841f039d35d73da84564963fb4b32dcb9000da2cb41

---

## Fast Path Benchmark Checklist

- [ ] Run Fast Path v1.0 evidence runner: `python3 demos/aem-evolve-multi-agent-api/tools/fast_path/run_fast_path_evidence_v1_0.py`
- [ ] Verify all 9 verdict files in `assurance/fast-path/v1/verdicts/`
- [ ] Record `evaluation_elapsed_ms` from each verdict file
- [ ] Confirm `full_assurance_recomputed_this_tick=false` in all verdicts
- [ ] Note scope: elapsed_ms covers Fast Path enforcement evaluation only, not full-system governance
- [ ] For independent benchmark: run in managed cloud environment and record elapsed_ms independently

---

## Report Template

Use `docs/reproduction/THIRD_PARTY_REPRODUCTION_REPORT_TEMPLATE.md` to document reproduction results.

---

## Claim Boundary Checklist

- [ ] For each gate with PASS outcome: confirm supporting artifact was AEM v1.1 verified
- [ ] For each gate with SCOPE_LIMITED: confirm scope qualifier is accurate
- [ ] For each gate with FAIL_CLOSED: confirm reason is documented
- [ ] No gate claims PASS without `artifact_verified = true`

---

## Known Limitations

1. v3.1 evidence execution is complete (PASS 12/12, EVIDENCE_PASS 9/9). External reproduction by an independent party has not been executed.
2. Fast Path benchmark results in `assurance/v4_0/evidence/V4_0_07_FAST_PATH_BENCHMARK_ARTIFACT.json` are from controlled local environment — not managed cloud. Independent benchmark required for v4.0.
3. Triple Anchor covers selected artifacts only — not universal. Existing anchor receipt covers pre-v3.1 state.
4. HSM-backed signing requires CloudHSM setup with `AEM_KMS_PROVIDER` env var. Not configured in controlled environment.
5. External security review is not part of reproduction kit scope — requires separate independent engagement.
6. 5/8 v4.0 acceptance criteria are PENDING_EXTERNAL — each has a controlled assessment artifact at `assurance/v4_0/evidence/`. External parties satisfy these criteria by executing independently.

---

## Submission Instructions

After completing reproduction:

1. Complete the `THIRD_PARTY_REPRODUCTION_REPORT_TEMPLATE.md`
2. Include all artifact hashes and verification results
3. Note any discrepancies from expected outputs
4. Submit report to EthicBit through the designated submission channel

---

## Non-Claims

This kit does not claim completed reproduction, external certification, production readiness, or regulatory approval.

---

*Third-Party Reproduction Kit v4.0 — EthicBit / CEMU v3.7.0+ — 2026-05-14*
