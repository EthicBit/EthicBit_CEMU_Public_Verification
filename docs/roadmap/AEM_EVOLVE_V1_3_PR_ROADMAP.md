# AEM-EVOLVE™ v1.3 — Gaps Closure Roadmap

**Version:** 1.3.0
**Base:** v1.2.0 (Mechanical Reasoning Layer)
**Objective:** Close all high/medium-priority gaps identified in the v1.2.0 technology audit.

---

## Gap inventory (from v1.2.0 audit)

| Gap | Priority | v1.3 PR |
|---|---|---|
| LLM Advisory Adapter — boundary defined, not implemented | Medium | PR 2 |
| ML-KEM768 runtime — documented, not in tree | Medium | PR 3 |
| HITL production-grade quorum model | High | PR 4 |
| PostgreSQL adapter — skeleton not activated | Low | PR 5 |
| Independent reproduction toolkit | High | PR 6 |

---

## PR sequence

| # | Branch | Title | Gap closed |
|---|---|---|---|
| PR 1 | `docs/aem-evolve-v1-3-roadmap` | docs: add AEM-EVOLVE™ v1.3 PR roadmap | Meta |
| PR 2 | `feat/aem-evolve-v1-3-llm-advisory-adapter` | feat: implement LLM advisory adapter | LLM Advisory Adapter |
| PR 3 | `feat/aem-evolve-v1-3-mlkem768-runtime` | feat: add ML-KEM768 post-quantum KEM runtime | ML-KEM768 |
| PR 4 | `feat/aem-evolve-v1-3-hitl-quorum` | feat: upgrade HITL to production-grade quorum model | HITL identity |
| PR 5 | `feat/aem-evolve-v1-3-postgresql-adapter` | feat: activate and validate PostgreSQL adapter | PostgreSQL |
| PR 6 | `docs/aem-evolve-v1-3-reproduction-toolkit` | docs: add independent reproduction toolkit + whitepaper v1.3 | Reproductions |

---

## PR 1 — Roadmap

**Branch:** `docs/aem-evolve-v1-3-roadmap`
**Files:** `docs/roadmap/AEM_EVOLVE_V1_3_PR_ROADMAP.md`
**Purpose:** Define v1.3 scope and gap closure map.

---

## PR 2 — LLM Advisory Adapter

**Branch:** `feat/aem-evolve-v1-3-llm-advisory-adapter`
**Files:**
- `tools/advisory/llm_advisory_adapter.py`
- `tools/advisory/LLM_ADVISORY_LOG.json` (generated)
- `docs/LLM_ADVISORY_ADAPTER_SPEC.md`

**Behaviour:**
- Reads sealed `MECH_REASON_REPORT.json` (already sealed — read-only)
- Calls Claude API (`claude-sonnet-4-6`) to generate advisory narrative
- Tags all output `advisory_only: true`, `governance_binding: false`
- Writes to `LLM_ADVISORY_LOG.json` — never to assurance artifacts
- Does NOT modify `report_hash`, `recommended_outcome`, or `triggered_rules`

**Constitutional constraint:** LLM advises. It does not govern.

**Expected output:** `LLM_ADVISORY_STATUS=PASS`

---

## PR 3 — ML-KEM768 Post-Quantum KEM Runtime

**Branch:** `feat/aem-evolve-v1-3-mlkem768-runtime`
**Files:**
- `tools/crypto/mlkem768_wrapper.py`
- `tools/crypto/verify_mlkem768.py`
- `assurance/evolve-multi-agent/v1_3/mlkem768_kem_report.json`
- `docs/MLKEM768_RUNTIME.md`

**Behaviour:**
- Key generation, encapsulation, decapsulation via `mlkem` package
- Graceful fallback to simulation mode if library unavailable
- Verification script confirms round-trip integrity
- Does NOT replace Ed25519/ML-DSA signing — adds KEM layer for runtime secret protection

**Expected output:** `MLKEM768_STATUS=PASS`

---

## PR 4 — HITL Production-Grade Quorum Model

**Branch:** `feat/aem-evolve-v1-3-hitl-quorum`
**Files:**
- `tools/hitl/hitl_quorum_verifier.py`
- `tools/hitl/HITL_QUORUM_POLICY.json`
- `assurance/evolve-multi-agent/v1_3/hitl_quorum_report.json`
- `docs/HITL_QUORUM_MODEL.md`

**Behaviour:**
- N-of-M quorum enforcement (e.g. 2-of-3 APPROVER signatures required)
- Time-bounded approval windows (configurable TTL per decision class)
- Per-approver Ed25519 canonical SHA-256 verification
- Quorum threshold enforcement: decision is invalid if < N approvals
- Emits `hitl_quorum_report.json` with per-approver verification results

**Expected output:** `HITL_QUORUM_VERIFICATION=PASS`

---

## PR 5 — PostgreSQL Adapter Activation

**Branch:** `feat/aem-evolve-v1-3-postgresql-adapter`
**Files:**
- `db_adapter.py` — add connection pool + health check to `PostgresAdapter`
- `tools/db/validate_postgres_adapter.py` — validates adapter contract without live DB
- `migrations/003_langraph_checkpointer.sql`
- `docs/POSTGRESQL_ADAPTER.md`

**Behaviour:**
- Completes `PostgresAdapter` with `ThreadedConnectionPool` (psycopg2)
- Health check method `ping() -> bool`
- Contract validator confirms all `DBAdapter` abstract methods are correctly implemented
- Documents LangGraph checkpointer migration path (SqliteSaver → PostgreSQL)

**Expected output:** `POSTGRES_ADAPTER_VALIDATION=PASS`

---

## PR 6 — Independent Reproduction Toolkit + Whitepaper v1.3

**Branch:** `docs/aem-evolve-v1-3-reproduction-toolkit`
**Files:**
- `tools/reproduction/run_full_verification.sh` — one-command full stack verification
- `tools/reproduction/verify_all_v1_3.py` — Python reproducer: runs all checks, emits summary
- `assurance/evolve-multi-agent/v1_3/REPRODUCTION_REPORT.json`
- `challenge/independent-reproduction/AEM_V1_3_INDEPENDENT_REPRODUCTION_CHALLENGE.md`
- `docs/whitepapers/WHITEPAPER_V1_3_AEM_EVOLVE_GAPS_CLOSURE.md`

**Behaviour:**
- `verify_all_v1_3.py` runs all v1.1 + v1.2 + v1.3 verification scripts end-to-end
- Emits a single `FULL_STACK_VERIFICATION=PASS | FAIL` with per-component results
- Challenge doc defines what counts as a valid external reproduction

**Expected output:** `FULL_STACK_VERIFICATION=PASS`

---

## Decision priority (unchanged from v1.2)

```
FAIL_CLOSED > ESCALATE_TO_HITL > SCOPE_LIMITED > PASS
```

## Non-claims (v1.3 transversal)

```
HITL quorum model is not HSM-backed.
HITL quorum model is not enterprise IAM.
ML-KEM768 wrapper is not a certified cryptographic implementation.
PostgreSQL adapter is not production-tested at scale.
LLM advisory output is not governance.
LLM advisory output does not override MECH-REASON™ recommended_outcome.
This release is not regulatory approval.
This release is not external certification.
```

---

## Status

| PR | Status |
|---|---|
| PR 1 — Roadmap | In progress |
| PR 2 — LLM Advisory Adapter | Pending |
| PR 3 — ML-KEM768 runtime | Pending |
| PR 4 — HITL quorum model | Pending |
| PR 5 — PostgreSQL adapter | Pending |
| PR 6 — Reproduction toolkit + whitepaper | Pending |
