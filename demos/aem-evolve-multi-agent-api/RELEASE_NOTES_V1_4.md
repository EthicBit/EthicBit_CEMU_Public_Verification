# AEM-EVOLVE™ Multi-Agent Governance API — Release Notes v1.4.0

**Release date:** 2026-05-09
**Git tag:** `v1.4.0`
**Branch:** `main`
**Base:** v1.3.0 — Gaps Closure
**Commit SHA:** `e3eda3ce`

---

## What is v1.4.0?

v1.4.0 closes all six production hardening gaps identified in the v1.3.0 audit. It does not change the core API surface or the MECH-REASON™ governance path. It extends the stack with: a production-grade signing abstraction, HMAC-token HITL identity verification, the real ML-KEM768 library, an async PostgreSQL adapter, and a CI-enforced full-stack reproduction workflow.

**v1.4 definition:**

```
v1.3 = v1.2 + LLM-advisory-bounded + ML-KEM768-runtime + HITL-quorum-enforced
             + PostgreSQL-activated + full-stack-reproducible

v1.4 = v1.3 + signing-provider-abstracted + HITL-identity-HMAC
             + ML-KEM768-real-library + PostgreSQL-async + CI-reproduction-gated
```

---

## What's new in v1.4.0

### PR #119 — Roadmap

- `docs/roadmap/AEM_EVOLVE_V1_4_PR_ROADMAP.md`

Documents all six gaps from the v1.3.0 audit mapped to 7 ordered PRs.

### PR #120 — SigningProvider Abstraction

- `tools/signing/signing_provider.py` — `SigningProvider` ABC (`sign`, `verify`, `public_key_pem`)
- `tools/signing/env_signing_provider.py` — reads Ed25519 key from `ETHICBIT_ED25519_PRIVATE_KEY_PEM` env var
- `tools/signing/file_signing_provider.py` — reads from file path (dev use)
- `tools/signing/verify_signing_provider.py` — 8-check round-trip verifier
- `assurance/evolve-multi-agent/v1_4/signing_provider_report.json`

### PR #121 — HITL HMAC-Token Identity Verifier

- `tools/hitl/HITL_IDENTITY_POLICY.json` — token TTL, shared-secret config, approver registry
- `tools/hitl/hitl_identity_verifier.py` — 10-check HMAC-SHA256 time-bounded token verification
- `tools/hitl/hitl_token_generator.py` — generates valid tokens for CI
- `assurance/evolve-multi-agent/v1_4/hitl_identity_report.json`

Token format: `HMAC-SHA256(secret, approver_id + ":" + event_id + ":" + timestamp_floor_minutes)`

### PR #122 — ML-KEM768 Library Activation

- `tools/crypto/mlkem768_wrapper.py` — corrected to use real `mlkem` library API
- `tools/crypto/mlkem768_setup_check.py` — 9-check library installation validator
- `assurance/evolve-multi-agent/v1_4/mlkem768_library_report.json`

Fixes incorrect API calls (`mlkem.keygen768()` → `kem.key_gen()`; `mlkem.enc768()` → `kem.encaps()` returning `(ss, ct)`).

### PR #123 — Async PostgreSQL Adapter

- `db_adapter.py` — adds `AsyncPostgresAdapter` using `asyncpg`
- `tools/db/validate_async_postgres_adapter.py` — 10-check contract validator
- `tools/db/postgres_mock_integration_test.py` — 6-check async mock test
- `migrations/004_indexes.sql` — performance indexes for production
- `assurance/evolve-multi-agent/v1_4/async_postgres_adapter_report.json`

### PR #124 — CI Reproduction Workflow + Dockerfile

- `.github/workflows/aem-evolve-reproduction.yml` — runs full-stack verifier on every push to main
- `Dockerfile.reproduction` — Python 3.11-slim reproduction container
- `tools/reproduction/verify_all_v1_4.py` — 14-check full-stack verifier
- `assurance/evolve-multi-agent/v1_4/REPRODUCTION_REPORT.json`

### PR #125 — Whitepaper v1.4

- `docs/whitepapers/WHITEPAPER_V1_4_AEM_EVOLVE_PRODUCTION_HARDENING.md`

---

## Verification results

All scripts verified on `main` at commit `e3eda3ce`:

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
| V1_4-SIGNING-PROVIDER | `verify_signing_provider.py` | `SIGNING_PROVIDER_VERIFICATION=PASS (8/8)` |
| V1_4-HITL-IDENTITY | `hitl_identity_verifier.py` | `HITL_IDENTITY_VERIFICATION=PASS (10/10)` |

Run all at once:

```bash
python3 demos/aem-evolve-multi-agent-api/tools/reproduction/verify_all_v1_4.py
# FULL_STACK_VERIFICATION=PASS  (14/14)
```

---

## Known limitations and non-claims

| Item | Status |
|---|---|
| SigningProvider | Not HSM-backed — ABC only |
| HITL identity | HMAC shared-secret is demo-grade — not enterprise IAM |
| ML-KEM768 | Not independently audited |
| AsyncPostgresAdapter | Not production-tested at scale |
| CI reproduction | Internal CI only — not external independent reproduction |
| Independent external reproductions | Challenge open — 0 received |
| Regulatory approval | Not claimed |
| External certification | Not certified |

---

## API surface changes

None. v1.4.0 is additive. No breaking changes.

`AsyncPostgresAdapter` is a new async adapter alongside `PostgresAdapter`. Activate with:

```python
adapter = await AsyncPostgresAdapter.create("postgresql://user:pass@host:5432/dbname")
```

---

## Upgrade notes from v1.3.0

No migration required. Pull `main` at tag `v1.4.0` and run the new full-stack verifier.

```bash
git pull origin main
git checkout v1.4.0
pip install cryptography mlkem asyncpg
python3 demos/aem-evolve-multi-agent-api/tools/reproduction/verify_all_v1_4.py
# FULL_STACK_VERIFICATION=PASS  (14/14)
```

---

## Core claim

> AEM-EVOLVE™ v1.4 closes all production hardening gaps from the v1.3.0 audit: signing provider abstraction, HMAC-token HITL identity, real ML-KEM768 library, async PostgreSQL adapter, and CI-enforced reproduction workflow. Full-stack verification: 14/14 checks pass.

## Non-claims (transversal v1.4)

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
