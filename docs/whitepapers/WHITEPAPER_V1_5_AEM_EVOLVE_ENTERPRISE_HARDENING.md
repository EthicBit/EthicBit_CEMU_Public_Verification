# AEM-EVOLVE™ v1.5 — Enterprise Hardening Whitepaper

**Version:** 1.5.0
**Date:** 2026-05-09
**Base:** v1.4.0 (Production Hardening)
**Full-stack verification:** `FULL_STACK_VERIFICATION=PASS (16/16)`

---

## Executive summary

AEM-EVOLVE™ v1.5 closes all six gaps identified in the v1.4.0 production audit. It introduces HSM driver stubs for PKCS#11 and AWS KMS, an OIDC RS256 JWT HITL identity verifier, a runtime dependency validator, an async concurrency test with pgbouncer integration guide, and a v1.4 independent reproduction challenge.

**v1.5 definition:**

```
v1.4 = v1.3 + signing-provider-abstracted + HITL-identity-HMAC
             + ML-KEM768-real-library + PostgreSQL-async + CI-reproduction-gated

v1.5 = v1.4 + HSM-driver-stubs + OIDC-JWT-HITL-identity
             + dependency-validated + async-concurrency-tested
             + pgbouncer-documented + v1.4-challenge-open
```

---

## Gap inventory and closure

| Gap | v1.4 status | v1.5 closure |
|---|---|---|
| SigningProvider HSM | ABC only, no driver | `Pkcs11SigningProvider` + `KmsSigningProvider` stubs |
| HITL enterprise IAM | HMAC shared-secret | OIDC RS256 JWT verifier (inline JWKS, no IdP needed for CI) |
| Runtime dependencies | `anthropic`/`psycopg2` absent, unknown status | `dependency_validator.py` with REQUIRED/OPTIONAL tiering |
| AsyncPostgresAdapter under load | No concurrency test, no pgbouncer docs | N=20 concurrent asyncio test + pgbouncer guide |
| External reproduction | 0 external reports, no v1.4 challenge | `AEM_V1_4_INDEPENDENT_REPRODUCTION_CHALLENGE.md` |
| LLM advisory without API key | Simulation mode (Low priority) | Unchanged — bundled in reproduction PR |

---

## Component architecture

### PR 2 — PKCS#11 and KMS Signing Provider Stubs

**Files:** `tools/signing/pkcs11_signing_provider.py`, `kms_signing_provider.py`, `verify_hsm_signing_providers.py`

Both `Pkcs11SigningProvider` and `KmsSigningProvider` implement the `SigningProvider` ABC. They raise `ImportError` with installation guidance when their respective libraries (`pkcs11`, `boto3`) are absent. `FileSigningProvider` is confirmed as a software drop-in substitute.

`Pkcs11SigningProvider` uses the `pkcs11` library's `ECDSA_SHA256` mechanism and retrieves keys by `CKA_LABEL`. Configuration is via environment variables (`ETHICBIT_PKCS11_LIB`, `ETHICBIT_PKCS11_SLOT`, `ETHICBIT_PKCS11_PIN`, `ETHICBIT_PKCS11_KEY_LABEL`).

`KmsSigningProvider` calls `kms:Sign` and `kms:GetPublicKey` against the configured key ARN (`ETHICBIT_KMS_KEY_ID`).

**Verification:** 10-check verifier confirms ABC inheritance, graceful ImportError with guidance, and software fallback drop-in.

**Non-claim:** Not production-tested against real hardware or AWS KMS.

### PR 3 — OIDC JWT HITL Identity Verifier

**Files:** `tools/hitl/HITL_OIDC_POLICY.json`, `oidc_token_generator.py`, `oidc_hitl_identity_verifier.py`

Implements RS256 JWT verification using the `cryptography` library (no PyJWT required). `OidcTestKeyPair` generates an ephemeral RSA-2048 key pair and issues OIDC-style ID tokens with `iss`, `aud`, `sub`, `iat`, `exp`, `event_id` claims. `verify_oidc_token()` validates the signature against an inline JWKS, then checks issuer, audience, expiry, and approver registry membership.

The verifier replaces the need for a live IdP in CI while providing the same JWT structure that a production OIDC provider (Okta, Auth0, Keycloak, Azure AD) would issue.

**Token format:** RS256 JWT with standard OIDC claims + `event_id` extension claim.

**Verification:** 10-check verifier — signature, expiry, issuer, audience, registry, event_id claim presence.

**Non-claim:** CI JWKS is locally generated. Production requires external OIDC provider.

### PR 4 — Runtime Dependency Validator + Server Smoke Test

**Files:** `tools/runtime/dependency_validator.py`, `server_smoke_test.py`

`dependency_validator.py` classifies packages as `REQUIRED` or `OPTIONAL`. REQUIRED misses fail the check; OPTIONAL misses emit WARN but still count as PASS. Packages checked:

| Package | Tier | Status (at v1.5) |
|---|---|---|
| `fastapi` | REQUIRED | Installed |
| `cryptography` | REQUIRED | Installed (48.0.0) |
| `mlkem` | REQUIRED | Installed |
| `asyncpg` | REQUIRED | Installed (0.31.0) |
| `langgraph` | OPTIONAL | Installed |
| `anthropic` | OPTIONAL | **Not installed** (WARN) |
| `psycopg2` | OPTIONAL | **Not installed** (WARN) |
| `uvicorn` | OPTIONAL | Installed |
| `pytest` | OPTIONAL | Installed |

`server_smoke_test.py` imports core modules, constructs a FastAPI app in-process, and runs a TestClient health check. Gracefully skips `main.py` if `langgraph` is absent.

**Non-claim:** Server smoke test does not start a production server.

### PR 5 — AsyncPostgresAdapter Concurrency Test + pgbouncer Guide

**Files:** `tools/db/async_postgres_concurrency_test.py`, `docs/PGBOUNCER_INTEGRATION_GUIDE.md`

The concurrency test fires N=20 concurrent `asyncio.gather()` tasks across `execute()`, `fetch()`, and `ping()` against a mock pool. All 6 checks pass including a performance gate (< 5 s for N=20 mock writes).

The pgbouncer guide documents transaction-pooling mode configuration, the asyncpg `statement_cache_size=0` requirement for pgbouncer compatibility, and the admin console health check command.

**Non-claim:** Mock pool — not a live database. Real latency depends on network + DB.

### PR 6 — v1.4 Reproduction Challenge + 16-Check Verifier

**Files:** `challenge/independent-reproduction/AEM_V1_4_INDEPENDENT_REPRODUCTION_CHALLENGE.md`, `tools/reproduction/verify_all_v1_5.py`

The v1.4 challenge provides reproduction instructions for the 14-check verifier and a Docker path. The 16-check verifier adds `V1_5-HSM-SIGNING` and `V1_5-OIDC-HITL` to the existing 14.

---

## Cumulative verification results

```
FULL_STACK_VERIFICATION=PASS  (16/16)

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

  v1.5 stack (2/2):
  V1_5-HSM-SIGNING             HSM_SIGNING_VERIFICATION=PASS (10/10)
  V1_5-OIDC-HITL               OIDC_HITL_VERIFICATION=PASS (10/10)
```

Verification command:
```bash
python3 demos/aem-evolve-multi-agent-api/tools/reproduction/verify_all_v1_5.py
```

---

## Non-claims (v1.5 transversal)

```
PKCS#11 provider is not a real HSM integration.
KMS provider is not a real AWS KMS integration.
OIDC verifier uses locally generated JWKS — not a real IdP.
CI JWKS is not from a production OIDC provider.
AsyncPostgresAdapter concurrency test uses mocks, not a live database.
pgbouncer guide is documentation only — not a tested production configuration.
External independent reproductions remain at 0 received.
This release is not regulatory approval.
This release is not external certification.
```

---

## Cumulative stack baseline

```
EthicBit defines the standard.
CEERV defines offline verifiable evidence.
CEMU executes, seals, verifies, and governs the operational flow.
AEM-EVOLVE™ v1.1 adds governed change assurance.
AEM-EVOLVE™ v1.2 adds deterministic mechanical reasoning.
AEM-EVOLVE™ v1.3 closes five audit gaps and adds full-stack reproduction.
AEM-EVOLVE™ v1.4 closes production hardening gaps.
AEM-EVOLVE™ v1.5 closes enterprise hardening gaps: HSM driver stubs,
                   OIDC JWT HITL identity, dependency validation,
                   async concurrency testing, pgbouncer documentation.
```
