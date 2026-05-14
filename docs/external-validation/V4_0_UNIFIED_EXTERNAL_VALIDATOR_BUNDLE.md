# EthicBit / AEM-EVOLVE v4.0 — Unified External Validator Bundle

**Criteria covered:** 1 (third-party reproduction) · 2 (external security review) · 8 (external claim review)
**Status:** ACTIVE — open for external engagement
**Release:** `aem-evolve-v4.0-controlled-evidence-2026-05-14`
**Constitutional dependency:** EthicBit / CEMU v3.7.0+
**Public mirror:** https://github.com/EthicBit/EthicBit_CEMU_Public_Verification

---

## What this bundle is

A single self-contained engagement package that allows any independent reviewer to satisfy up to three v4.0 acceptance criteria in one session:

| Criterion | What you do | Time |
|---|---|---|
| 1 — Third-party reproduction | Clone, run scripts, compare results | ~20 min |
| 2 — Security review | Inspect posture, triage findings | ~30–60 min |
| 8 — Claim review | Verify claims against evidence | ~20 min |

You can complete one, two, or all three. Each has independent value.

**No secrets. No keys. No cloud credentials. No proprietary access required.**
Everything runs from the public mirror using only what is in the repository.

---

## Prerequisites

- Python 3.11+
- git
- Internet connection (for Sepolia RPC anchor verification)
- No cloud account, no API keys, no database setup required

---

## Setup — do this once

```bash
git clone https://github.com/EthicBit/EthicBit_CEMU_Public_Verification
cd EthicBit_CEMU_Public_Verification
git checkout aem-evolve-v4.0-controlled-evidence-2026-05-14

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Record your environment:
```bash
python3 --version
uname -a   # or systeminfo on Windows
git rev-parse HEAD
```

---

## Part A — Criterion 1: Third-Party Reproduction

**Goal:** Confirm that the evidence artifacts produce the same results in your independent environment.

### A1. Run AI-ME v3.1 evidence (12-gate evaluation)

```bash
python3 demos/aem-evolve-multi-agent-api/tools/ai_me/run_ai_me_evidence_v3_1.py
```

**Expected:** `PASS 12/12 gates, artifact_verified=true all gates`
**Output file:** `assurance/ai-me/v3_1/AI_ME_V3_1_AGGREGATE_REPORT.json`

### A2. Run Fast Path v1.0 evidence (9 scenarios)

```bash
python3 demos/aem-evolve-multi-agent-api/tools/fast_path/run_fast_path_evidence_v1_0.py
```

**Expected:** `EVIDENCE_PASS 9/9 scenarios, 7/7 mandatory rules verified`
**Output file:** `assurance/fast-path/v1/FAST_PATH_VERIFICATION_REPORT.json`

### A3. Verify AEM v1.1 artifact hashes (12 artifacts)

```bash
python3 - <<'EOF'
import json, hashlib
from pathlib import Path
receipts = sorted(Path('assurance/ai-me/v3_1').glob('receipt_AI-ME-*.json'))
for receipt in receipts:
    r = json.load(open(receipt))
    declared = r['artifact_hash']
    computed = hashlib.sha256(Path(r['artifact_path']).read_bytes()).hexdigest()
    result = 'MATCH' if declared == computed else f'MISMATCH declared={declared[:12]} computed={computed[:12]}'
    print(f"{receipt.stem[-6:]}: {result}")
EOF
```

**Expected:** 12 × MATCH

### A4. Verify v4.0 criterion artifacts present and populated

```bash
python3 - <<'EOF'
import json
from pathlib import Path
for i in range(1, 9):
    p = Path(f'assurance/v4_0/evidence/V4_0_0{i}_{"REPRODUCTION_KIT,SECURITY_REVIEW,CLOUD_DEPLOYMENT,HSM_SIGNING,AEM_REVERIFICATION,TRIPLE_ANCHOR,FAST_PATH_BENCHMARK,CLAIM_REVIEW".split(",")[i-1]}_ARTIFACT.json')
    if p.exists():
        d = json.loads(p.read_bytes())
        print(f"C{i}: {d.get('controlled_status','?')} — {list(d.keys())[2]}")
    else:
        print(f"C{i}: MISSING — {p.name}")
EOF
```

**Expected:** 8 artifacts present — 3 CONTROLLED_PASS, 5 PENDING_EXTERNAL

### A5. Verify Sepolia on-chain anchor (v4.0)

```bash
python3 - <<'EOF'
import json, urllib.request
receipt = json.load(open('assurance/v4_0/V4_0_CONTROLLED_EVIDENCE_ANCHOR_RECEIPT.json'))
tx = receipt['tx_hash']
body = json.dumps({"jsonrpc":"2.0","id":1,"method":"eth_getTransactionByHash","params":[tx]}).encode()
req = urllib.request.Request(
    'https://sepolia.gateway.tenderly.co', data=body,
    headers={"Content-Type":"application/json"})
res = json.loads(urllib.request.urlopen(req, timeout=20).read())
print('ON_CHAIN' if res.get('result') else 'NOT_FOUND', f"block={int(res['result']['blockNumber'],16)}" if res.get('result') else '')
EOF
```

**Expected:** `ON_CHAIN block=10852797`

### A6. Verify Ethereum mainnet anchor (v4.0)

```bash
python3 - <<'EOF'
import json, urllib.request
receipt = json.load(open('assurance/v4_0/V4_0_MAINNET_ANCHOR_RECEIPT.json'))
tx = receipt['tx_hash']
body = json.dumps({"jsonrpc":"2.0","id":1,"method":"eth_getTransactionByHash","params":[tx]}).encode()
req = urllib.request.Request(
    'https://ethereum-rpc.publicnode.com', data=body,
    headers={"Content-Type":"application/json"})
res = json.loads(urllib.request.urlopen(req, timeout=20).read())
print('ON_CHAIN' if res.get('result') else 'NOT_FOUND', f"block={int(res['result']['blockNumber'],16)}" if res.get('result') else '')
EOF
```

**Expected:** `ON_CHAIN block=25095358`

Or verify directly: https://etherscan.io/tx/0xd5fe44459f15e1cb3230f841f039d35d73da84564963fb4b32dcb9000da2cb41

---

## Part B — Criterion 2: Security Review

**Goal:** Independently assess the security posture of the governance stack. No penetration testing required — static review of documented controls is sufficient for the baseline. Pentest is a bonus.

### B1. Review security and threat model documents

```
demos/aem-evolve-multi-agent-api/docs/SECURITY_REVIEW.md
demos/aem-evolve-multi-agent-api/docs/THREAT_MODEL.md
```

Review against the governance attack surfaces: fast path bypass, claim boundary override, artifact hash manipulation, replay attacks, HITL identity spoofing.

### B2. Review governance security controls (7 controls)

These controls are documented in `SECURITY_REVIEW.md` and implemented in the codebase:

| Control | Review question |
|---|---|
| HITL Identity Enforcement (HMAC + OIDC) | Is identity enforced fail-closed? |
| Audit Chain Integrity (SHA-256 hash-linked) | Can the chain be silently broken? |
| Replay Mitigation (hitl_used_tokens) | Are replay attacks blocked? |
| RBAC Access Control (X-API-Key fail-closed) | Does missing key deny access? |
| Input Validation (Pydantic field validators) | Are inputs validated at API boundary? |
| KMS/HSM Signing (ProductionKmsProvider) | Is the signing provider pluggable to real KMS? |
| Monitoring and Alerting (Prometheus counters) | Are governance events observable? |

### B3. Review static analysis results

```bash
# Review pre-run results
cat demos/aem-evolve-multi-agent-api/tools/security/static_analysis_2026_05.json | python3 -m json.tool | head -60

# Optionally re-run bandit yourself
pip install bandit
bandit -r demos/aem-evolve-multi-agent-api/ -ll 2>/dev/null | tail -20
```

**Known internal findings:** HIGH=0, MEDIUM=11 (B608/B306/B310 — reviewed as false positives, parameterized queries and controlled URLs). Confirm or dispute disposition.

### B4. Review dependency CVE state

```bash
# Review pre-run results
cat demos/aem-evolve-multi-agent-api/tools/security/dependency_scan_2026_05.json | python3 -m json.tool

# Optionally re-run pip-audit
pip install pip-audit
pip-audit -r demos/aem-evolve-multi-agent-api/requirements.txt
```

**Known state:** 0 CVEs in API production dependencies. 15 CVEs in tooling packages (gitpython, pip, setuptools, urllib3) — all documented as non-API-runtime scope. Confirm or dispute scope classification.

### B5. Review Fast Path enforcement security

```bash
# Read the Fast Path gate implementation
cat demos/aem-evolve-multi-agent-api/tools/fast_path/fast_path_gate.py | head -80
```

Key questions: Can the ceiling be bypassed? Can a FAIL_CLOSED verdict be upgraded? Is the snapshot immutable during evaluation?

### B6. Review signing mechanism

```bash
# View signing provider interface (no private key content)
cat demos/aem-evolve-multi-agent-api/tools/signing/signing_provider.py
cat demos/aem-evolve-multi-agent-api/tools/signing/production_kms_provider.py | head -40
```

Note: current environment uses Ed25519 file-based signing (demo tier). Production path to KMS is documented but not provisioned. Criterion 4 covers HSM/KMS separately.

---

## Part C — Criterion 8: Claim Review

**Goal:** Verify that all public claims are supported by reproducible evidence and that no overclaims exist.

### C1. Review each public claim

After completing Part A, you have reproduced the evidence. Now verify each claim:

| ID | Claim | Evidence to check | Expected verdict |
|---|---|---|---|
| CA-01 | v4.0 external validation process initiated | `assurance/v4_0/V4_0_EXTERNAL_VALIDATION_INITIATION_RECORD.json` | SUPPORTED |
| CA-02 | AI-ME v3.1 PASS 12/12 gates | `assurance/ai-me/v3_1/AI_ME_V3_1_AGGREGATE_REPORT.json` + your A1 result | SUPPORTED |
| CA-03 | Fast Path v1.0 EVIDENCE_PASS 9/9 | `assurance/fast-path/v1/FAST_PATH_VERIFICATION_REPORT.json` + your A2 result | SUPPORTED |
| CA-04 | Sepolia anchor block 10840044 | `assurance/v4_0/V4_0_SEPOLIA_ANCHOR_RECEIPT.json` + your A5 result | SUPPORTED (testnet scope) |
| CA-05 | AEM reverification 12/12 | `assurance/v4_0/evidence/V4_0_05_AEM_REVERIFICATION_ARTIFACT.json` + your A3 result | SUPPORTED |
| CA-06 | Triple anchor on-chain | `assurance/v4_0/evidence/V4_0_06_TRIPLE_ANCHOR_ARTIFACT.json` + A5+A6 results | SUPPORTED (scoped) |
| CA-07 | Fast Path benchmark 9 scenarios | `assurance/v4_0/evidence/V4_0_07_FAST_PATH_BENCHMARK_ARTIFACT.json` | SUPPORTED |

### C2. Verify non-claims are correctly absent

Check README.md and the status bulletins in `docs/` for the following — none should be asserted:

```
v4.0 validated              — must NOT appear as a positive claim
third-party reproduced      — must NOT appear as a positive claim
externally certified        — must NOT appear as a positive claim
production-ready            — must NOT appear as a positive claim
HSM-backed signing active   — must NOT appear as a positive claim
full_assurance_recomputed_per_tick=true — must NOT appear as a positive claim
```

### C3. Claim boundary enforcement

```bash
cat assurance/ai-me/v3_1/evidence/AI_ME_12_claim_boundary_enforcement_artifact.json | python3 -m json.tool | grep -E '"fail_closed|violations|aggregate'
```

**Expected:** `fail_closed_violations: 0`, `aggregate_outcome: PASS`

### C4. Flag any overclaims or gaps

If you find a claim that is not supported by the evidence you reproduced, document it. If you find a claim that should exist but does not, document that too. Both are valid findings.

---

## Output — complete the report template

Use `docs/reproduction/THIRD_PARTY_REPRODUCTION_REPORT_TEMPLATE.md` **or** the unified template below.

The unified template is at:
`docs/external-validation/V4_0_UNIFIED_EXTERNAL_VALIDATOR_REPORT_TEMPLATE.md`

Return the completed report to EthicBit. Partial reports (completing only Part A, or only Part C) are valid and valuable.

---

## What you are NOT being asked to do

- Certify EthicBit or AEM-EVOLVE for any purpose
- Approve regulatory compliance or clinical use
- Validate financial or investment claims
- Confirm production readiness
- Perform a formal penetration test (welcome but not required)
- Sign any legal agreement

---

## Non-claims

This bundle does not claim third-party reproduction, external security review, or external claim review has been completed. Those criteria are satisfied only when an independent reviewer with no EthicBit affiliation submits a completed report. Completing this bundle in your environment constitutes independent evidence for the criteria you cover.

---

*EthicBit / AEM-EVOLVE v4.0 Unified External Validator Bundle — EthicBit / CEMU v3.7.0+ — 2026-05-14*
