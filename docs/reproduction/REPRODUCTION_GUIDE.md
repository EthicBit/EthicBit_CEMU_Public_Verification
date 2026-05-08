# AEM-EVOLVE™ Multi-Agent Governance API — Independent Reproduction Guide

**Version:** v0.3.1-demo  
**Pinned commit:** `c634f906`  
**Assurance ladder milestone:** Phase 1 — Foundation & Independent Verification

---

## Purpose

This guide enables any party with standard developer tooling to independently reproduce the AEM-EVOLVE™ Multi-Agent Governance API controlled execution demonstration from a clean environment. Independent reproduction means executing in a separate environment, not inspecting outputs produced by EthicBit.

---

## What "Reproduction" Means Here

| In scope | Out of scope |
|---|---|
| Cloning the repo at the pinned commit | Evaluating correctness of governance logic |
| Running the file integrity check | Auditing cryptographic key generation |
| Verifying Ed25519 signatures with the published public key | Reproducing the Ethereum mainnet anchor transaction |
| Running the E2E smoke test end-to-end | Validating production readiness |
| Recording a structured reproduction report | Providing regulatory or clinical assessment |

---

## Prerequisites

| Tool | Minimum version | Check |
|---|---|---|
| `git` | any | `git --version` |
| `python3` | 3.10 | `python3 --version` |
| `pip` | any | `pip --version` |
| `openssl` | 1.1+ | `openssl version` |
| `curl` | any | `curl --version` |
| `bash` | 3.2+ | `bash --version` |

---

## Environment Setup

Reproduce in one of:
- A fresh Linux VM (Ubuntu 22.04+ recommended)
- A fresh macOS environment (12+)
- A Docker container: `python:3.11-slim` + `apt install openssl curl git`
- GitHub Codespaces (standard image)

**Do not reproduce in the same environment where EthicBit generated the artifacts.** Independent reproduction requires a separate environment.

---

## Step-by-Step Instructions

### 1. Clone and checkout the pinned commit

```bash
git clone https://github.com/EthicBit/EthicBit_CEMU.git
cd EthicBit_CEMU
git checkout c634f906
git log --oneline -1  # must show: c634f906
```

### 2. Verify file integrity (no server needed)

```bash
python3 scripts/core/run_aem_evolve_multi_agent_reproduction_challenge.py
```

Expected:
```
AEM_EVOLVE_REPRODUCTION_CHALLENGE_STATUS=ALL_MATCH
```

Record the output verbatim in your reproduction report.

### 3. Verify Ed25519 signatures (no server needed)

```bash
bash demos/aem-evolve-multi-agent-api/scripts/verify_demo_receipt_signatures.sh
```

Expected:
```
AEM_EVOLVE_MULTI_AGENT_API_DEMO_SIGNATURE_STATUS=PASS
```

The public key used for verification is at:  
`assurance/evolve-multi-agent/AEM_EVOLVE_MULTI_AGENT_API_DEMO_PUBLIC_KEY.pem`

This is a demo key — locally verifiable, not HSM-backed.

### 4. Install Python dependencies

```bash
cd demos/aem-evolve-multi-agent-api
pip install -r requirements.txt
```

### 5. Start the API server (terminal 1)

```bash
python main.py
```

The server starts on `http://127.0.0.1:8000`. Structured JSON logs will appear on stdout.

### 6. Run the E2E smoke test (terminal 2)

```bash
bash scripts/run_demo_e2e.sh
```

Expected output includes all of:
```
AEM_EVOLVE_MULTI_AGENT_API_DEMO_STATUS=PASS
EVOLUTION_EVENT_CREATED=PASS
EVOLUTION_RECEIPT_CREATED=PASS
HITL_APPROVAL_GATE=PASS
AUDIT_TABLES=PASS
SIGNATURE_STATUS=NOT_SIGNED_DEMO
ANCHOR_STATUS=NOT_ANCHORED_FOR_THIS_DEMO
```

### 7. Verify auth controls

```bash
bash scripts/verify_auth_controls.sh
```

Expected: 3 checks return 401 (no key), 3 return 403 (wrong role), 2 return the correct role response.

### 8. Run tamper checklist

```bash
bash scripts/run_tamper_checklist.sh
```

Expected: `SIMULATED_TAMPER_CHECKLIST=PASS`

### 9. Verify the audit chain

```bash
python3 ../../scripts/core/verify_aem_evolve_multi_agent_audit_chain.py
```

Expected: `AEM_EVOLVE_AUDIT_CHAIN_STATUS=PASS`

---

## Evaluation Criteria

| Check | Expected result | Pass condition |
|---|---|---|
| File integrity | `ALL_MATCH` | All declared subjects match SHA-256 |
| Ed25519 signatures | `PASS` | Both anchor_receipt and manifest verify |
| E2E smoke test | `PASS` | All sub-checks pass |
| Auth controls | 401/403/role-pass | Fail-closed on unauthorized paths |
| Tamper checklist | `PASS` | Tamper detection works |
| Audit chain | `PASS` | Hash-linked chain intact |

---

## Reporting

After completing all steps, fill in `docs/reproduction/REPRODUCTION_REPORT_TEMPLATE.md` and submit it:

1. Fork `EthicBit/EthicBit_CEMU`.
2. Copy the template to `independent-reproductions/REPORT_<your-handle>_<date>.md`.
3. Fill in all fields honestly, including any failures or deviations.
4. Open a pull request to `main` with title: `reproduction: <your-handle> v0.3.1-demo <date>`.

Partial reproductions (some checks pass, some fail) are also valuable — do not omit failures.

---

## Scope Boundary

This reproduction confirms that the demo software runs as described. It does not confirm:
- Production readiness.
- Regulatory or clinical validity.
- Independent security assessment.
- Correctness of governance logic beyond the behavioral claims listed above.

See `demos/aem-evolve-multi-agent-api/docs/SCOPE_BOUNDARY.md` for the full boundary statement.
