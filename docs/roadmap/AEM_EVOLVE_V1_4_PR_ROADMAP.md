# AEM-EVOLVE™ v1.4 — Production Hardening Roadmap

**Version:** 1.4.0
**Base:** v1.3.0 (Gaps Closure)
**Objective:** Close all remaining gaps from the v1.3.0 audit.

---

## Gap inventory (from v1.3.0 audit)

| Gap | Priority | v1.4 PR |
|---|---|---|
| Ed25519 / ML-DSA signing — demo-grade stubs | High | PR 2 |
| HITL identity — demo-grade approver verification | High | PR 3 |
| ML-KEM768 — simulation mode, no certified library | Medium | PR 4 |
| PostgreSQL — not production-tested; sync-only | Medium | PR 5 |
| Independent reproductions — 0 external reports; no CI check | High | PR 6 |
| LLM advisory — simulation mode without API key | Low | bundled in PR 6 |

---

## PR sequence

| # | Branch | Title | Gap |
|---|---|---|---|
| PR 1 | `docs/aem-evolve-v1-4-roadmap` | docs: add AEM-EVOLVE™ v1.4 roadmap | Meta |
| PR 2 | `feat/aem-evolve-v1-4-signing-provider` | feat: add production-grade signing provider abstraction | Ed25519/ML-DSA |
| PR 3 | `feat/aem-evolve-v1-4-hitl-identity` | feat: add HITL HMAC-token identity verifier | HITL identity |
| PR 4 | `feat/aem-evolve-v1-4-mlkem768-library` | feat: activate mlkem library and upgrade wrapper | ML-KEM768 |
| PR 5 | `feat/aem-evolve-v1-4-postgresql-async` | feat: add async PostgreSQL adapter + integration tests | PostgreSQL |
| PR 6 | `feat/aem-evolve-v1-4-ci-reproduction` | feat: add CI reproduction workflow + Dockerfile | Reproductions |
| PR 7 | `docs/aem-evolve-v1-4-whitepaper` | docs: add AEM-EVOLVE™ v1.4 whitepaper | — |

---

## PR 2 — Signing Provider Abstraction

**Branch:** `feat/aem-evolve-v1-4-signing-provider`
**Files:**
- `tools/signing/signing_provider.py` — `SigningProvider` ABC (`sign`, `verify`, `public_key_pem`)
- `tools/signing/env_signing_provider.py` — reads Ed25519 private key from `ETHICBIT_ED25519_PRIVATE_KEY_PEM` env var
- `tools/signing/file_signing_provider.py` — reads from file path (dev use)
- `tools/signing/verify_signing_provider.py` — round-trip verifier
- `assurance/evolve-multi-agent/v1_4/signing_provider_report.json`

**Non-claims:** Not HSM-backed. HSM integration requires hardware implementation of `SigningProvider` ABC.
**Expected output:** `SIGNING_PROVIDER_VERIFICATION=PASS`

---

## PR 3 — HITL HMAC-Token Identity Verifier

**Branch:** `feat/aem-evolve-v1-4-hitl-identity`
**Files:**
- `tools/hitl/hitl_identity_verifier.py` — HMAC-SHA256 time-bounded token verification
- `tools/hitl/HITL_IDENTITY_POLICY.json` — token TTL, shared-secret config, approver registry
- `tools/hitl/hitl_token_generator.py` — generates valid test tokens for CI
- `assurance/evolve-multi-agent/v1_4/hitl_identity_report.json`

**Token format:** `HMAC-SHA256(secret, approver_id + ":" + event_id + ":" + timestamp_floor_minutes)`
**Non-claims:** Not enterprise IAM. Shared secret is demo-grade. HSM-backed identity requires external IdP.
**Expected output:** `HITL_IDENTITY_VERIFICATION=PASS`

---

## PR 4 — ML-KEM768 Library Activation

**Branch:** `feat/aem-evolve-v1-4-mlkem768-library`
**Files:**
- `tools/crypto/mlkem768_wrapper.py` — updated to use real `mlkem` library API correctly
- `tools/crypto/mlkem768_setup_check.py` — validates library installation and API
- `assurance/evolve-multi-agent/v1_4/mlkem768_library_report.json`

**Behaviour:** Replaces simulation mode with real `mlkem` library (FIPS 203). Falls back to simulation only if library not installed.
**Expected output:** `MLKEM768_LIBRARY_STATUS=PASS  mode=mlkem`

---

## PR 5 — Async PostgreSQL Adapter + Integration Tests

**Branch:** `feat/aem-evolve-v1-4-postgresql-async`
**Files:**
- `db_adapter.py` — add `AsyncPostgresAdapter` using `asyncpg`
- `tools/db/validate_async_postgres_adapter.py` — contract validator (no live DB)
- `tools/db/postgres_mock_integration_test.py` — mock-based integration test
- `migrations/004_indexes.sql` — performance indexes for production
- `assurance/evolve-multi-agent/v1_4/async_postgres_adapter_report.json`

**Expected output:** `ASYNC_POSTGRES_ADAPTER_VALIDATION=PASS`

---

## PR 6 — CI Reproduction Workflow + Dockerfile

**Branch:** `feat/aem-evolve-v1-4-ci-reproduction`
**Files:**
- `.github/workflows/aem-evolve-reproduction.yml` — runs `verify_all_v1_3.py` on every push to main
- `Dockerfile.reproduction` — zero-dependency reproduction container (Python 3.11-slim)
- `tools/reproduction/verify_all_v1_4.py` — updated 14-check full-stack verifier (adds v1.4 checks)
- `assurance/evolve-multi-agent/v1_4/REPRODUCTION_REPORT.json`

**Expected output:** `FULL_STACK_VERIFICATION=PASS (14/14)`

---

## PR 7 — Whitepaper v1.4

**Branch:** `docs/aem-evolve-v1-4-whitepaper`
**Files:** `docs/whitepapers/WHITEPAPER_V1_4_AEM_EVOLVE_PRODUCTION_HARDENING.md`

---

## Non-claims (v1.4 transversal)

```
SigningProvider is not HSM-backed.
HITL identity is not enterprise IAM.
HITL tokens are not production-grade without external IdP.
AsyncPostgresAdapter is not production-tested at scale.
ML-KEM768 is not independently audited.
CI reproduction is not external independent reproduction.
This release is not regulatory approval.
This release is not external certification.
```
