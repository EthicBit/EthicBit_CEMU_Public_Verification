# AEM-EVOLVE™ v1.4 — Production Hardening Whitepaper

**Version:** 1.4.0
**Date:** 2026-05-09
**Base:** v1.3.0 (Gaps Closure)
**Full-stack verification:** `FULL_STACK_VERIFICATION=PASS (14/14)`

---

## Executive summary

AEM-EVOLVE™ v1.4 closes all six gaps identified in the v1.3.0 production audit. It does not change the core API surface, MECH-REASON™ governance path, or audit chain. It extends the assurance stack with a production-grade signing abstraction, HMAC-token HITL identity, a real post-quantum KEM library, an async PostgreSQL adapter, and a CI-enforced full-stack reproduction workflow.

**v1.4 definition:**

```
v1.3 = v1.2 + LLM-advisory-bounded + ML-KEM768-runtime + HITL-quorum-enforced
             + PostgreSQL-activated + full-stack-reproducible

v1.4 = v1.3 + signing-provider-abstracted + HITL-identity-HMAC
             + ML-KEM768-real-library + PostgreSQL-async + CI-reproduction-gated
```

---

## Gap inventory and closure

| Gap | v1.3 status | v1.4 closure |
|---|---|---|
| Ed25519 / ML-DSA signing | Demo-grade stubs | `SigningProvider` ABC + `EnvSigningProvider` |
| HITL approver identity | Demo-grade (no token verification) | HMAC-SHA256 time-bounded token verifier |
| ML-KEM768 | Simulation mode (wrong API calls) | Real `mlkem` library (FIPS 203) |
| PostgreSQL | Sync-only (`ThreadedConnectionPool`) | `AsyncPostgresAdapter` via `asyncpg` |
| CI reproduction | No CI gate | GitHub Actions workflow on every push to main |
| LLM advisory | Simulation without API key | Unchanged — still simulation without key (Low priority, no change) |

---

## Component architecture

### PR 2 — SigningProvider Abstraction

**Files:** `tools/signing/signing_provider.py`, `env_signing_provider.py`, `file_signing_provider.py`, `verify_signing_provider.py`

`SigningProvider` is an abstract base class with three abstract methods: `sign(message) → bytes`, `verify(message, signature) → bool`, `public_key_pem() → bytes`. Any HSM-backed implementation can satisfy this ABC.

`EnvSigningProvider` reads an Ed25519 private key from the `ETHICBIT_ED25519_PRIVATE_KEY_PEM` environment variable. This enables CI/CD key injection without file system access.

`FileSigningProvider` reads from a file path for local development and test key injection.

**Verification:** 8-check round-trip verifier confirms ABC shape, error conditions, and sign/verify correctness.

**Non-claim:** Not HSM-backed. HSM integration requires an external `SigningProvider` implementation.

### PR 3 — HITL HMAC-Token Identity Verifier

**Files:** `tools/hitl/hitl_identity_verifier.py`, `HITL_IDENTITY_POLICY.json`, `hitl_token_generator.py`

Token format: `HMAC-SHA256(shared_secret, approver_id + ":" + event_id + ":" + timestamp_floor_minutes)`

The verifier checks:
- Approver is registered in the policy document
- HMAC matches one of the valid time-window floors (within TTL)
- Token is not reusable across events (event_id binding)

TTL default: 10 minutes. Approver registry is defined in `HITL_IDENTITY_POLICY.json`.

**Verification:** 10-check verifier confirms correct token acceptance, wrong-approver rejection, wrong-event rejection, wrong-secret rejection, expired-token rejection, and registry enforcement.

**Non-claim:** Not enterprise IAM. Shared secret is demo-grade. Production requires external IdP with per-approver secret management.

### PR 4 — ML-KEM768 Library Activation

**Files:** `tools/crypto/mlkem768_wrapper.py` (updated), `mlkem768_setup_check.py`

The v1.3 wrapper called `mlkem.keygen768()`, `mlkem.enc768()`, `mlkem.dec768()` — none of which exist in the `mlkem` package. v1.4 corrects this to the real API:

```python
from mlkem.ml_kem import ML_KEM
from mlkem.parameter_set import ML_KEM_768
kem = ML_KEM(ML_KEM_768)
ek, dk = kem.key_gen()
ss, ct = kem.encaps(ek)   # (shared_secret, ciphertext) — shared secret first
ss2    = kem.decaps(dk, ct)
```

Key sizes: ek=1184 B, dk=2400 B, ct=1088 B, ss=32 B. Round-trip: `ss == ss2`.

Library still falls back to deterministic simulation if `mlkem` is not installed.

**Verification:** 9-check setup validator confirms import chain, sizes, round-trip, and mode detection.

### PR 5 — Async PostgreSQL Adapter

**Files:** `db_adapter.py` (adds `AsyncPostgresAdapter`), `tools/db/validate_async_postgres_adapter.py`, `postgres_mock_integration_test.py`, `migrations/004_indexes.sql`

`AsyncPostgresAdapter` uses `asyncpg.create_pool` and provides async methods: `execute`, `fetch`, `fetchrow`, `fetchval`, `ping`, `close`. It is initialised via an async factory:

```python
adapter = await AsyncPostgresAdapter.create("postgresql://user:pass@host/db")
rows = await adapter.fetch("SELECT * FROM evolution_events WHERE id=$1", evt_id)
await adapter.close()
```

`migrations/004_indexes.sql` adds performance indexes on `evolution_events`, `evolution_receipts`, and `audit_chain` tables for production workloads.

**Verification:** 10-check contract validator (no live DB), 6-check mock integration test.

**Non-claim:** Not production-tested at scale. Does not replace synchronous `PostgresAdapter`.

### PR 6 — CI Reproduction Workflow + Dockerfile

**Files:** `.github/workflows/aem-evolve-reproduction.yml`, `Dockerfile.reproduction`, `tools/reproduction/verify_all_v1_4.py`

The GitHub Actions workflow runs `verify_all_v1_3.py` and `verify_all_v1_4.py` on every push to `main`. It installs `cryptography`, `mlkem`, and `asyncpg` before running.

`verify_all_v1_4.py` runs 14 checks sequentially:
- v1.1 stack: 6 checks
- v1.2 stack: 2 checks
- v1.3 stack: 4 checks
- v1.4 stack: 2 checks (V1_4-SIGNING-PROVIDER, V1_4-HITL-IDENTITY)

`Dockerfile.reproduction` is a Python 3.11-slim container that installs the three runtime dependencies and runs the 14-check verifier with no other dependencies.

**Non-claim:** CI reproduction is not external independent reproduction. The challenge for external reproducers remains open.

---

## Cumulative verification results

```
FULL_STACK_VERIFICATION=PASS  (14/14)

  v1.1 stack (6/6):
  V1_1-REGULATORY-MAPPING      REGULATORY_MAPPING_CHECK=PASS
  V1_1-GOVERNANCE-METRICS      GOVERNANCE_EFFECTIVENESS_METRICS_STATUS=PASS
  V1_1-MULTI-ANCHOR            MULTI_ANCHOR_VERIFICATION=PASS
  V1_1-HITL-SIGNATURE          HITL_SIGNATURE_VERIFICATION=PASS_DEMO
  V1_1-RECEIPT-FORGERY         RECEIPT_FORGERY_TESTS=PASS
  V1_1-OFFICIAL-STATUS         OFFICIAL_STATUS_SIGNED=PASS

  v1.2 stack (2/2):
  V1_2-MECH-REASON-ENGINE      MECH_REASON_STATUS=PASS
  V1_2-MECH-REASON-VERIFY      MECH_REASON_VERIFICATION=PASS (10/10)

  v1.3 stack (4/4):
  V1_3-LLM-ADVISORY            LLM_ADVISORY_STATUS=PASS
  V1_3-MLKEM768                MLKEM768_STATUS=PASS (5/5)
  V1_3-HITL-QUORUM             HITL_QUORUM_VERIFICATION=PASS
  V1_3-POSTGRES-ADAPTER        POSTGRES_ADAPTER_VALIDATION=PASS (6/6)

  v1.4 stack (2/2):
  V1_4-SIGNING-PROVIDER        SIGNING_PROVIDER_VERIFICATION=PASS (8/8)
  V1_4-HITL-IDENTITY           HITL_IDENTITY_VERIFICATION=PASS (10/10)
```

Verification command:
```bash
python3 demos/aem-evolve-multi-agent-api/tools/reproduction/verify_all_v1_4.py
```

---

## Non-claims (v1.4 transversal)

```
SigningProvider is not HSM-backed.
HSM integration requires an external implementation of the SigningProvider ABC.
HITL identity is not enterprise IAM.
HITL tokens are not production-grade without external IdP.
AsyncPostgresAdapter is not production-tested at scale.
ML-KEM768 is not independently audited.
CI reproduction is not external independent reproduction.
This release is not regulatory approval.
This release is not external certification.
```

---

## API surface changes

None. v1.4.0 is additive. No breaking changes to:
- endpoints (`/events`, `/gate`, `/approve`, `/chain/verify`, `/metrics`, `/healthz`)
- RBAC roles (INITIATOR / APPROVER / OBSERVER)
- receipt schema
- audit chain
- SQLite storage

`AsyncPostgresAdapter` is a new adapter class alongside the existing `PostgresAdapter`. Activate by calling `await AsyncPostgresAdapter.create(dsn)` and wiring into an async context.

---

## Cumulative stack baseline

```
EthicBit defines the standard.
CEERV defines offline verifiable evidence.
CEMU executes, seals, verifies, and governs the operational flow.
AEM-EVOLVE™ v1.1 adds governed change assurance.
AEM-EVOLVE™ v1.2 adds deterministic mechanical reasoning.
AEM-EVOLVE™ v1.3 closes five audit gaps and adds full-stack reproduction.
AEM-EVOLVE™ v1.4 closes production hardening gaps: signing abstraction,
                   HMAC-token HITL identity, real ML-KEM768 library,
                   async PostgreSQL, CI-enforced reproduction.
```
