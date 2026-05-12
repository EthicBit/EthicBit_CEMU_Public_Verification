# Third-Party Reproduction Kit v4.0

**Document type:** Reproduction Kit  
**Version:** 4.0 (Scaffold)  
**Status:** `SCAFFOLD — awaiting v3.1 evidence execution`  
**Constitutional dependency:** EthicBit / CEMU v3.7.0+  
**Date:** 2026-05-12

---

## Overview

This kit enables independent third parties to reproduce EthicBit AEM-EVOLVE v4.0 evidence in an independent environment.

**Current state:** Scaffold. v3.1 evidence execution has not been completed. This kit defines the reproduction procedure for when it is.

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

### Run AI-ME gate scaffold

```bash
# Verify scaffold compiles
python3 -m py_compile demos/aem-evolve-multi-agent-api/tools/ai_me/common.py
python3 -m py_compile demos/aem-evolve-multi-agent-api/tools/ai_me/verify_ai_me_01_model_evaluation.py

# Run scaffold aggregator (no evidence yet — will produce MISSING outcomes)
python3 -c "
from demos.aem_evolve_multi_agent_api.tools.ai_me.aggregate_ai_me_v3_1 import aggregate
result = aggregate()
import json; print(json.dumps(result, indent=2))
"
```

---

## Expected Evidence Outputs (when v3.1 evidence is executed)

Each AI-ME gate produces a JSON report at:
```
assurance/ai-me/v3_1/AI-ME-0X_report.json
```

Expected acceptance criteria per gate are defined in:
```
docs/ai-me/AI_ME_GATE_MATRIX_V3_1.json
```

---

## Hash Verification Instructions (AEM v1.1)

For each evidence artifact:

```bash
# Compute SHA-256 hash
sha256sum <artifact_path>

# Compare against declared hash in manifest
cat assurance/evolve-multi-agent/AEM_EVOLVE_MULTI_AGENT_API_MANIFEST.json | python3 -c "
import json, sys
manifest = json.load(sys.stdin)
# Find artifact and compare declared hash
"
```

---

## AEM v1.1 Artifact Verification Checklist

- [ ] All required artifacts listed in `AI_ME_GATE_MATRIX_V3_1.json` are present
- [ ] SHA-256 hash of each artifact matches declared hash in AEM v1.1 manifest
- [ ] Verification receipts exist for each verified artifact
- [ ] Public anchor references verified where anchor receipts exist

---

## Triple Anchor Verification Checklist

- [ ] Identify artifacts with `public_anchor_references` in their verification receipts
- [ ] Verify anchor receipt at `docs/anchors/AEM_V1_1_MAINNET_ANCHOR_RECEIPT.json`
- [ ] Confirm anchored hash matches artifact hash
- [ ] Note: Not all artifacts are anchored. Only artifacts with specific anchor receipts are covered.

---

## Fast Path Benchmark Checklist

- [ ] Deploy Fast Path scaffold (`demos/aem-evolve-multi-agent-api/tools/fast_path/`)
- [ ] Create test canonical snapshot using `fast_path_snapshot.create_scaffold_snapshot()`
- [ ] Run `verify_fast_path.verify_scaffold()` and measure elapsed time
- [ ] Record elapsed_ms from verdict output
- [ ] Note scope: elapsed_ms covers Fast Path enforcement evaluation only, not full-system governance

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

1. v3.1 is Specification Release only — evidence execution is not yet complete
2. Fast Path benchmark results require managed cloud environment for valid measurement
3. Triple Anchor covers selected artifacts only — not universal
4. HSM-backed signing requires CloudHSM setup not yet documented for v4.0
5. External security review is not part of reproduction kit scope — it requires a separate engagement

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

*Third-Party Reproduction Kit v4.0 — EthicBit / CEMU v3.7.0+ — 2026-05-12*
