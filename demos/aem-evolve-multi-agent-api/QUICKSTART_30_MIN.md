# AEM-EVOLVE™ Multi-Agent Governance API — Quickstart (30 min)

**Version:** v0.3.1-demo  
**Pinned commit:** `c634f906`  
**Goal:** Reach `AEM_EVOLVE_MULTI_AGENT_API_DEMO_STATUS=PASS` from a clean clone in under 30 minutes.

---

## Prerequisites

- `git`, `python3 >= 3.10`, `pip`, `openssl`, `curl`, `bash`

---

## Step 1 — Clone and checkout (2 min)

```bash
git clone https://github.com/EthicBit/EthicBit_CEMU.git
cd EthicBit_CEMU
git checkout c634f906
```

---

## Step 2 — File integrity check (1 min)

```bash
python3 scripts/core/run_aem_evolve_multi_agent_reproduction_challenge.py
```

Expected: `AEM_EVOLVE_REPRODUCTION_CHALLENGE_STATUS=ALL_MATCH`

---

## Step 3 — Signature verification (1 min)

```bash
bash demos/aem-evolve-multi-agent-api/scripts/verify_demo_receipt_signatures.sh
```

Expected: `AEM_EVOLVE_MULTI_AGENT_API_DEMO_SIGNATURE_STATUS=PASS`

---

## Step 4 — Install dependencies (5 min)

```bash
cd demos/aem-evolve-multi-agent-api
pip install -r requirements.txt
```

---

## Step 5 — Start the API server (terminal 1)

```bash
python main.py
```

Wait for: `Uvicorn running on http://127.0.0.1:8000`

---

## Step 6 — Run E2E smoke test (terminal 2, 2 min)

```bash
bash scripts/run_demo_e2e.sh
```

Expected output includes:

```
AEM_EVOLVE_MULTI_AGENT_API_DEMO_STATUS=PASS
EVOLUTION_EVENT_CREATED=PASS
EVOLUTION_RECEIPT_CREATED=PASS
HITL_APPROVAL_GATE=PASS
AUDIT_TABLES=PASS
```

---

## Step 7 — Verify auth controls (1 min)

```bash
bash scripts/verify_auth_controls.sh
```

Expected: 3× 401, 3× 403, 2× correct-role PASS.

---

## Step 8 — Verify audit chain (1 min)

```bash
python3 ../../scripts/core/verify_aem_evolve_multi_agent_audit_chain.py
```

Expected: `AEM_EVOLVE_AUDIT_CHAIN_STATUS=PASS`

---

## Step 9 — Record your result

Fill in `docs/reproduction/REPRODUCTION_REPORT_TEMPLATE.md` and submit to `independent-reproductions/` via pull request.

---

## Troubleshooting

| Symptom | Fix |
|---|---|
| `ModuleNotFoundError: langgraph` | `pip install -r requirements.txt` |
| Port 8000 in use | `lsof -i :8000` then kill the process |
| `openssl: command not found` | `brew install openssl` (macOS) or `apt install openssl` |
| `SIGNATURE_VERIFY = FAIL` | Ensure you are on commit `c634f906` with no local modifications |
| `ALL_MATCH` fails for `main.py` | Stash local changes: `git stash` |

---

## What this verifies

| Check | What it confirms |
|---|---|
| File integrity | All declared files match expected SHA-256s |
| Ed25519 signatures | Anchor receipt and manifest are signed with the demo public key |
| E2E smoke test | Evolution Event → Receipt → HITL gate flow works end-to-end |
| Auth controls | RBAC fail-closed behavior on 401/403 paths |
| Audit chain | Hash-linked chain is intact |

**Note:** This is a technical demonstration. See `docs/SCOPE_BOUNDARY.md` for what this demo does and does not claim.
