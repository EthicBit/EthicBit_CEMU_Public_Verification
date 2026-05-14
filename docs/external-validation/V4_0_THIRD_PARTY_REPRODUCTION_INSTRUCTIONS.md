# v4.0 Third-Party Reproduction Instructions

**Criterion:** 1 — third_party_reproduction
**Status:** PENDING_EXTERNAL
**Controlled assessment:** CONTROLLED_SELF_REPRODUCTION_PASS (2026-05-14)
**Artifact:** `assurance/v4_0/evidence/V4_0_01_REPRODUCTION_KIT_ARTIFACT.json`
**Release:** `aem-evolve-v4.0-controlled-evidence-2026-05-14`
**Constitutional dependency:** EthicBit / CEMU v3.7.0+

---

## What this criterion requires

An independent third party — with no EthicBit affiliation — reproduces the controlled evidence in a genuinely separate environment and issues a report confirming or denying the expected outputs. A controlled self-reproduction by EthicBit does NOT satisfy this criterion.

---

## What was already verified internally

The controlled self-reproduction (2026-05-14) confirmed:

| Step | Result |
|---|---|
| AI-ME v3.1 aggregate report | PASS 12/12 gates |
| Fast Path v1.0 verification report | EVIDENCE_PASS 9/9 scenarios |
| AEM v1.1 hash verification (12 artifacts) | all_match=true |
| Sepolia anchor on-chain RPC verification | block 10840044, confirmed |
| v4.0 controlled evidence report | 3 CONTROLLED_PASS, 5 PENDING_EXTERNAL |

---

## What the external reviewer must do

### 1. Clone from public mirror

```bash
git clone https://github.com/EthicBit/EthicBit_CEMU_Public_Verification
cd EthicBit_CEMU_Public_Verification
git checkout aem-evolve-v4.0-controlled-evidence-2026-05-14
```

### 2. Set up independent environment

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Environment must be independent — separate machine, VM, or cloud instance not controlled by EthicBit.

### 3. Run AI-ME v3.1 evidence

```bash
python3 demos/aem-evolve-multi-agent-api/tools/ai_me/run_ai_me_evidence_v3_1.py
```

Expected: `PASS 12/12 gates, artifact_verified=true all gates`
Output: `assurance/ai-me/v3_1/AI_ME_V3_1_AGGREGATE_REPORT.json`

### 4. Run Fast Path v1.0 evidence

```bash
python3 demos/aem-evolve-multi-agent-api/tools/fast_path/run_fast_path_evidence_v1_0.py
```

Expected: `EVIDENCE_PASS 9/9 scenarios, 7/7 mandatory rules verified`
Output: `assurance/fast-path/v1/FAST_PATH_VERIFICATION_REPORT.json`

### 5. Verify AEM v1.1 artifact hashes

```bash
python3 -c "
import json, hashlib
from pathlib import Path
for receipt in sorted(Path('assurance/ai-me/v3_1').glob('receipt_AI-ME-*.json')):
    r = json.load(open(receipt))
    declared = r['artifact_hash']
    computed = hashlib.sha256(Path(r['artifact_path']).read_bytes()).hexdigest()
    match = 'MATCH' if declared == computed else 'MISMATCH'
    print(f'{receipt.name}: {match}')
"
```

Expected: 12 × MATCH

### 6. Verify Sepolia on-chain anchor

```bash
python3 -c "
import json, urllib.request
receipt = json.load(open('assurance/v4_0/V4_0_CONTROLLED_EVIDENCE_ANCHOR_RECEIPT.json'))
tx = receipt['tx_hash']
rpc = 'https://sepolia.gateway.tenderly.co'
body = json.dumps({'jsonrpc':'2.0','id':1,'method':'eth_getTransactionByHash','params':[tx]}).encode()
req = urllib.request.Request(rpc, data=body, headers={'Content-Type': 'application/json'})
res = json.loads(urllib.request.urlopen(req, timeout=20).read())
print('ON_CHAIN' if res.get('result') else 'NOT_FOUND', tx[:18])
"
```

---

## Required output

Complete `docs/reproduction/THIRD_PARTY_REPRODUCTION_REPORT_TEMPLATE.md` and include:

- Reviewer name / organization (no EthicBit affiliation)
- Review date
- Environment used (OS, Python version, cloud provider if applicable)
- Commit or tag checked out
- Commands executed
- Hash verification output (per artifact)
- AI-ME v3.1 result
- Fast Path v1.0 result
- Anchor verification result
- PASS / FAIL / PARTIAL per step
- Deviations from expected outputs
- Signature or attestation

---

## Non-claim

This document does not constitute third-party reproduction. Reproduction is only satisfied when an independent party with no EthicBit affiliation completes the above steps in a separate environment and submits a report.
