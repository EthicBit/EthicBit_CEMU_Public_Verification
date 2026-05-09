# AEM-EVOLVE™ v1.3 — Gaps Closure
## Whitepaper

**Version:** 1.3.0
**Status:** Released
**Predecessor:** AEM-EVOLVE™ v1.2 — Mechanical Reasoning Layer (Whitepaper v1.2)

---

## Abstract

AEM-EVOLVE™ v1.3 closes five gaps identified in the v1.2.0 technology audit: the LLM Advisory Adapter, the ML-KEM768 post-quantum KEM runtime, the HITL production-grade quorum model, the PostgreSQL adapter activation, and the independent reproduction toolkit. All gaps are closed with deterministic verification scripts. The full-stack verifier (`verify_all_v1_3.py`) runs 12 checks across the v1.1 + v1.2 + v1.3 stack and produces `FULL_STACK_VERIFICATION=PASS`.

---

## 1. Gap inventory and closure

| Gap | Priority | Closed by | Verification output |
|---|---|---|---|
| LLM Advisory Adapter — boundary defined, not implemented | Medium | PR 2 | `LLM_ADVISORY_STATUS=PASS` |
| ML-KEM768 runtime — documented, not in tree | Medium | PR 3 | `MLKEM768_STATUS=PASS` |
| HITL production-grade quorum model | High | PR 4 | `HITL_QUORUM_VERIFICATION=PASS` |
| PostgreSQL adapter — skeleton not activated | Low | PR 5 | `POSTGRES_ADAPTER_VALIDATION=PASS` |
| Independent reproduction toolkit | High | PR 6 | `FULL_STACK_VERIFICATION=PASS` |

---

## 2. LLM Advisory Adapter (PR 2)

### What it does

Reads the sealed `MECH_REASON_REPORT.json` after sealing and calls the Claude API (`claude-sonnet-4-6`) to generate a plain-language advisory narrative for human reviewers (HITL briefing).

### Constitutional constraints (unchanged from v1.2)

- LLM receives only sealed outputs — never raw evidence
- LLM writes to `LLM_ADVISORY_LOG.json` only — never to assurance artifacts
- Output tagged `advisory_only: true`, `governance_binding: false`
- `report_hash` is computed before LLM interaction — LLM output is not an input to `report_hash`
- LLM cannot modify `recommended_outcome`

### Simulation mode

Without `ANTHROPIC_API_KEY`, the adapter runs in simulation mode and logs a placeholder narrative. `LLM_ADVISORY_STATUS=PASS` in both cases — the check validates boundary compliance, not LLM output quality.

---

## 3. ML-KEM768 Post-Quantum KEM Runtime (PR 3)

### What it implements

`mlkem768_wrapper.py` provides key generation, encapsulation, and decapsulation for ML-KEM768 (FIPS 203, formerly Kyber768) — the NIST-standardized post-quantum KEM.

Library priority:
1. `mlkem` package (real FIPS 203 implementation)
2. `kyber-py` package
3. Simulation mode (deterministic test vectors — NOT cryptographically secure)

Simulation mode is clearly marked and uses SHAKE-256 with nonce-embedding in the ciphertext to maintain round-trip integrity without a real KEM library.

### Role in the stack

ML-KEM768 is for runtime secret protection — protecting symmetric keys in transit. It does NOT replace Ed25519/ML-DSA signing on the governance path. The signing layer remains unchanged.

### Verification (5 checks)

C-01 key sizes · C-02 ciphertext/shared-secret sizes · C-03 round-trip integrity · C-04 randomness · C-05 key isolation.

---

## 4. HITL Production-Grade Quorum Model (PR 4)

### Decision classes

| Class | Quorum | TTL | TTL enforcement |
|---|---|---|---|
| STANDARD | 1-of-1 | 24h | warn (demo data) |
| HIGH_RISK | 2-of-3 | 1h | strict |
| FAIL_CLOSED_OVERRIDE | 3-of-3 | 30min | strict |

### Verification (5 checks per decision group)

C-A role validation · C-B decision validity · C-C TTL enforcement · C-D canonical SHA-256 hash · C-E quorum count (unique approvers, no duplicates).

### Remaining gap

Approver identity remains demo-grade. Real production requires HSM-backed key custody or enterprise IAM — this is documented as a non-claim, not over-claimed.

---

## 5. PostgreSQL Adapter Activation (PR 5)

### What changed from v1.2 skeleton

| Capability | v1.2 skeleton | v1.3 activated |
|---|---|---|
| Connection pooling | Not present | `ThreadedConnectionPool(minconn, maxconn)` |
| Health check | Not present | `ping() -> bool` |
| Graceful shutdown | Not present | `close_pool()` |
| Contract validation | Not present | 6-check `validate_postgres_adapter.py` |
| LangGraph migration | Documented | `migrations/003_langraph_checkpointer.sql` added |

The contract validator (`POSTGRES_ADAPTER_VALIDATION=PASS`) confirms the full `DBAdapter` abstract interface is satisfied without requiring a live PostgreSQL instance.

---

## 6. Independent Reproduction Toolkit (PR 6)

### `verify_all_v1_3.py`

Runs 12 checks across the full stack:

| Layer | Checks |
|---|---|
| v1.1 | 6 (regulatory mapping, governance metrics, multi-anchor, HITL signature, receipt forgery, official status) |
| v1.2 | 2 (MECH-REASON engine, MECH-REASON verifier) |
| v1.3 | 4 (LLM advisory, ML-KEM768, HITL quorum, PostgreSQL adapter) |

### Reproduction challenge

Anyone cloning at `v1.3.0` can run `verify_all_v1_3.py` with Python ≥ 3.11 and no additional packages. No network access required. Expected output: `FULL_STACK_VERIFICATION=PASS`.

---

## 7. Cumulative stack

```
EthicBit — constitutional governance core
  └── CEERV — offline verifiable evidence
        └── CEMU — operational capsule
              └── AEM-EVOLVE™ v1.0 — API governance + runtime
                    └── v1.1 — governed change assurance
                          └── v1.2 — mechanical reasoning layer
                                └── v1.3 — gaps closure  ← this release
```

---

## 8. Remaining non-closed gaps

| Item | Status after v1.3 |
|---|---|
| Ed25519 / ML-DSA production key custody | Still demo-grade (GitHub Secrets only) |
| HITL enterprise IAM | Not implemented — non-claim preserved |
| ML-KEM768 with certified library | Simulation mode by default |
| PostgreSQL production-tested at scale | Not tested |
| Independent external reproductions | Challenge open — 0 received |

---

## 9. Claim

> AEM-EVOLVE™ v1.3 closes the five gaps identified in the v1.2.0 audit: LLM advisory adapter, ML-KEM768 KEM runtime, HITL quorum model, PostgreSQL adapter activation, and independent reproduction toolkit. Full-stack verification: 12/12 checks pass.

## Non-claims (transversal v1.3)

```
HITL quorum model is not HSM-backed.
HITL quorum model is not enterprise IAM.
ML-KEM768 wrapper is not a certified cryptographic implementation.
Simulation mode is NOT cryptographically secure.
PostgreSQL adapter is not production-tested at scale.
LLM advisory output is not governance.
LLM advisory output does not override MECH-REASON™ recommended_outcome.
This release is not regulatory approval.
This release is not external certification.
```
