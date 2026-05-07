# AEM-EVOLVE Multi-Agent Governance API — Independent Reproduction Challenge

**Version:** 0.3.1-demo  
**Source commit:** `7aa52723`  
**Assurance ladder milestone:** PR 5 — Independent Reproduction Challenge

---

## What This Is

An external-ready package that allows any party with `git`, `python3 (>=3.10)`, and `openssl` to independently verify the AEM-EVOLVE Multi-Agent Governance API demonstration from a clean clone.

## What This Is NOT

- This is **not** a claim of independent reproduction. Independent reproduction requires execution in a separate environment by a third party.
- This does **not** claim production readiness, regulatory approval, or certification.

---

## Prerequisites

- `git`
- `python3 >= 3.10`
- `pip`
- `openssl` (for signature verification)
- `curl` (for live endpoint checks)
- `bash`

---

## Steps

### 1. Clone and checkout the pinned commit

```bash
git clone https://github.com/EthicBit/EthicBit_CEMU.git
cd EthicBit_CEMU
git checkout 7aa52723
```

### 2. Verify file integrity (no server needed)

```bash
python3 scripts/core/run_aem_evolve_multi_agent_reproduction_challenge.py
```

Expected: `AEM_EVOLVE_REPRODUCTION_CHALLENGE_STATUS=ALL_MATCH` (16/16 subjects)

### 3. Verify Ed25519 signatures (no server needed)

```bash
bash demos/aem-evolve-multi-agent-api/scripts/verify_demo_receipt_signatures.sh
```

Expected: `AEM_EVOLVE_MULTI_AGENT_API_DEMO_SIGNATURE_STATUS=PASS`

### 4. Start the API server (terminal 1)

```bash
cd demos/aem-evolve-multi-agent-api
pip install -r requirements.txt
python main.py
```

### 5. Run E2E smoke test (terminal 2)

```bash
bash demos/aem-evolve-multi-agent-api/scripts/run_demo_e2e.sh
```

Expected output includes:
```
AEM_EVOLVE_MULTI_AGENT_API_DEMO_STATUS=PASS
EVOLUTION_EVENT_CREATED=PASS
EVOLUTION_RECEIPT_CREATED=PASS
HITL_APPROVAL_GATE=PASS
AUDIT_TABLES=PASS
SIGNATURE_STATUS=NOT_SIGNED_DEMO
ANCHOR_STATUS=NOT_ANCHORED_FOR_THIS_DEMO
```

### 6. Run tamper checklist (terminal 2)

```bash
bash demos/aem-evolve-multi-agent-api/scripts/run_tamper_checklist.sh
```

Expected: `SIMULATED_TAMPER_CHECKLIST=PASS`

### 7. Verify the audit chain

```bash
python3 scripts/core/verify_aem_evolve_multi_agent_audit_chain.py
```

Expected: `AEM_EVOLVE_AUDIT_CHAIN_STATUS=PASS`

---

## Challenge Artifacts

| Artifact | Path |
|---|---|
| Challenge package | `assurance/evolve-multi-agent/AEM_EVOLVE_MULTI_AGENT_API_REPRODUCTION_CHALLENGE.json` |
| Local self-check report | `assurance/evolve-multi-agent/AEM_EVOLVE_MULTI_AGENT_API_REPRODUCTION_REPORT.json` |
| Challenge runner | `scripts/core/run_aem_evolve_multi_agent_reproduction_challenge.py` |
| Demo public key | `assurance/evolve-multi-agent/AEM_EVOLVE_MULTI_AGENT_API_DEMO_PUBLIC_KEY.pem` |

---

## On-Chain Reference

The demo manifest was anchored on Ethereum mainnet at:

- **TX:** `0x30fc9e6c810078c42ac1b840c3712d165342436ec427471b7f955425ea4b8275`
- **Block:** 25045091
- **Explorer:** https://etherscan.io/tx/0x30fc9e6c810078c42ac1b840c3712d165342436ec427471b7f955425ea4b8275

---

## Assurance Ladder Position

| PR | Milestone | Status |
|---|---|---|
| 1 | Demo Package | merged |
| 2 | Demo Mainnet Anchor | merged |
| 3 | Signed Demo Evolution Receipts | merged |
| 4 | Tamper-Evident Audit Chain | merged |
| **5** | **Independent Reproduction Challenge** | **this PR** |
| 6 | Production Authentication / Authorization | future |
| 7 | Production-Readiness Hardening | future |
| 8+ | External Review / Certification | conditional |
| 9+ | Regulatory Pathway | conditional |
| 10+ | Clinical / Diagnostic Pathway | conditional |
