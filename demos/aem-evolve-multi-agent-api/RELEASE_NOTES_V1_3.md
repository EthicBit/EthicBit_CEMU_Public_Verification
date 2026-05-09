# AEM-EVOLVE™ Multi-Agent Governance API — Release Notes v1.3.0

**Release date:** 2026-05-09
**Git tag:** `v1.3.0`
**Branch:** `main`
**Base:** v1.2.0 — Mechanical Reasoning Layer
**Commit SHA:** `da36ac12`

---

## What is v1.3.0?

v1.3.0 closes all five gaps identified in the v1.2.0 technology audit. It does not change the core API surface or the MECH-REASON™ governance path. It extends the stack with: a constitutional LLM advisory adapter, a post-quantum KEM runtime, a production-grade HITL quorum model, an activated PostgreSQL adapter, and a full-stack independent reproduction toolkit.

**v1.3 definition:**

```
v1.2 = v1.1 + mechanically-reasoning, policy-bound, LLM-free in governance path

v1.3 = v1.2 + LLM-advisory-bounded + ML-KEM768-runtime + HITL-quorum-enforced
             + PostgreSQL-activated + full-stack-reproducible
```

---

## What's new in v1.3.0

### PR #113 — Roadmap

- `docs/roadmap/AEM_EVOLVE_V1_3_PR_ROADMAP.md`

Documents all five gaps from the v1.2.0 audit mapped to 6 ordered PRs with branch names, file lists, expected outputs, and non-claims.

### PR #114 — LLM Advisory Adapter

- `tools/advisory/llm_advisory_adapter.py`
- `docs/LLM_ADVISORY_ADAPTER_SPEC.md`
- `assurance/evolve-multi-agent/v1_3/LLM_ADVISORY_LOG.json`

Implements the adapter defined in `OPTIONAL_LLM_ADVISORY_ADAPTER_BOUNDARY.md`. Reads the sealed `MECH_REASON_REPORT.json` (read-only, post-hoc) and calls `claude-sonnet-4-6` to generate a plain-language advisory narrative for HITL reviewers.

Enforcement:
- `advisory_only: true` on every output
- `governance_binding: false` on every output
- `source_report_hash` preserved unchanged from sealed report
- LLM output does NOT enter `report_hash` computation
- LLM output cannot modify `recommended_outcome`

Simulation mode: if `ANTHROPIC_API_KEY` is not set, runs in simulation mode. `LLM_ADVISORY_STATUS=PASS` in both cases.

### PR #115 — ML-KEM768 Post-Quantum KEM Runtime

- `tools/crypto/mlkem768_wrapper.py`
- `tools/crypto/verify_mlkem768.py`
- `assurance/evolve-multi-agent/v1_3/mlkem768_kem_report.json`

Provides key generation, encapsulation, and decapsulation for ML-KEM768 (FIPS 203). Library priority: `mlkem` → `kyber-py` → simulation mode.

Simulation mode design: PK embedded in SK (mirrors real ML-KEM768 SK format); nonce embedded in first 32 bytes of CT; decapsulation recovers shared secret from `(SK[-1184:], CT[:32])` without external library.

5-check verifier: key sizes · ciphertext/shared-secret sizes · round-trip integrity · randomness · key isolation.

Does NOT replace Ed25519/ML-DSA signing on the governance path.

### PR #116 — HITL Production-Grade Quorum Model

- `tools/hitl/HITL_QUORUM_POLICY.json`
- `tools/hitl/hitl_quorum_verifier.py`
- `assurance/evolve-multi-agent/v1_3/hitl_quorum_report.json`

Three decision classes with N-of-M quorum enforcement:

| Class | Quorum | TTL | TTL mode |
|---|---|---|---|
| STANDARD | 1-of-1 | 24h | warn (demo/historical) |
| HIGH_RISK | 2-of-3 | 1h | strict |
| FAIL_CLOSED_OVERRIDE | 3-of-3 | 30min | strict |

5 checks per decision group: role validation · decision validity · TTL enforcement · canonical SHA-256 · unique-approver quorum count.

Remaining limitation: approver identity is demo-grade. Real production requires HSM or enterprise IAM — this is preserved as a non-claim.

### PR #117 — PostgreSQL Adapter Activation

- `db_adapter.py` (upgraded from skeleton)
- `tools/db/validate_postgres_adapter.py`
- `migrations/003_langraph_checkpointer.sql`

PostgresAdapter upgraded from documented skeleton to active:

| Capability | Before | After |
|---|---|---|
| Connection pooling | Bare `psycopg2.connect` | `ThreadedConnectionPool(minconn, maxconn)` |
| Health check | Not present | `ping() -> bool` |
| Graceful shutdown | Not present | `close_pool()` |

6-check contract validator confirms full `DBAdapter` abstract interface is satisfied without requiring a live PostgreSQL instance. `migrations/003_langraph_checkpointer.sql` provides the LangGraph checkpointer schema for PostgreSQL.

### PR #118 — Independent Reproduction Toolkit + Whitepaper v1.3

- `tools/reproduction/verify_all_v1_3.py`
- `assurance/evolve-multi-agent/v1_3/REPRODUCTION_REPORT.json`
- `challenge/independent-reproduction/AEM_V1_3_INDEPENDENT_REPRODUCTION_CHALLENGE.md`
- `docs/whitepapers/WHITEPAPER_V1_3_AEM_EVOLVE_GAPS_CLOSURE.md`

`verify_all_v1_3.py` runs 12 checks end-to-end across the full stack. No additional packages required. No network required. Python ≥ 3.11 only.

---

## Verification results

All scripts verified on `main` at commit `da36ac12`:

| Check | Script | Result |
|---|---|---|
| V1_1-REGULATORY-MAPPING | `regulatory_mapping_checker.py` | `REGULATORY_MAPPING_CHECK=PASS` |
| V1_1-GOVERNANCE-METRICS | `governance_effectiveness_metrics.py` | `GOVERNANCE_EFFECTIVENESS_METRICS_STATUS=PASS` |
| V1_1-MULTI-ANCHOR | `multi_anchor_verifier.py` | `MULTI_ANCHOR_VERIFICATION=PASS` |
| V1_1-HITL-SIGNATURE | `HITL_signature_verifier.py` | `HITL_SIGNATURE_VERIFICATION=PASS_DEMO` |
| V1_1-RECEIPT-FORGERY | `test_receipt_forgery.py` | `RECEIPT_FORGERY_TESTS=PASS` |
| V1_1-OFFICIAL-STATUS | `official_status_signer.py` | `OFFICIAL_STATUS_SIGNED=PASS` |
| V1_2-MECH-REASON-ENGINE | `mech_reason.py` | `MECH_REASON_STATUS=PASS` |
| V1_2-MECH-REASON-VERIFY | `verify_mech_reason.py` | `MECH_REASON_VERIFICATION=PASS (10/10)` |
| V1_3-LLM-ADVISORY | `llm_advisory_adapter.py` | `LLM_ADVISORY_STATUS=PASS` |
| V1_3-MLKEM768 | `verify_mlkem768.py` | `MLKEM768_STATUS=PASS (5/5)` |
| V1_3-HITL-QUORUM | `hitl_quorum_verifier.py` | `HITL_QUORUM_VERIFICATION=PASS` |
| V1_3-POSTGRES-ADAPTER | `validate_postgres_adapter.py` | `POSTGRES_ADAPTER_VALIDATION=PASS (6/6)` |

Run all at once:

```bash
python3 demos/aem-evolve-multi-agent-api/tools/reproduction/verify_all_v1_3.py
# FULL_STACK_VERIFICATION=PASS  (12/12)
```

---

## Known limitations and non-claims

| Item | Status |
|---|---|
| HITL approver identity | Demo-grade — not HSM-backed, not enterprise IAM |
| ML-KEM768 | Simulation mode by default — not a certified implementation |
| PostgreSQL adapter | Not production-tested at scale |
| LLM advisory adapter | Simulation mode without `ANTHROPIC_API_KEY` |
| Ed25519 / ML-DSA key custody | GitHub Secrets only — not HSM |
| Independent external reproductions | Challenge open — 0 received |
| Regulatory approval | Not claimed |
| External certification | Not certified |

---

## API surface changes

None. v1.3.0 is additive. No breaking changes to:

- endpoints (`/events`, `/gate`, `/approve`, `/chain/verify`, `/metrics`, `/healthz`)
- RBAC roles (INITIATOR / APPROVER / OBSERVER)
- receipt schema
- audit chain
- SQLite storage

`PostgresAdapter` is a drop-in replacement for `SQLiteAdapter` — activate by setting `AEM_DB_URL` and swapping the adapter instance in `main.py`.

---

## Upgrade notes from v1.2.0

No migration required. Pull `main` at tag `v1.3.0` and run the new full-stack verifier.

```bash
git pull origin main
git checkout v1.3.0
python3 demos/aem-evolve-multi-agent-api/tools/reproduction/verify_all_v1_3.py
# FULL_STACK_VERIFICATION=PASS
```

---

## Core claim

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
