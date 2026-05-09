# AEM-EVOLVE™ v1.5 — Enterprise Hardening Roadmap

**Version:** 1.5.0
**Base:** v1.4.0 (Production Hardening)
**Objective:** Close all remaining gaps from the v1.4.0 audit.

---

## Gap inventory (from v1.4.0 audit)

| Gap | Priority | v1.5 PR |
|---|---|---|
| SigningProvider HSM-backed — ABC only, no HSM driver | High | PR 2 |
| HITL identity — HMAC shared-secret, not enterprise IAM | High | PR 3 |
| Runtime dependencies — psycopg2 / langgraph / anthropic absent | Medium | PR 4 |
| AsyncPostgresAdapter — no concurrency test, no pgbouncer guide | Medium | PR 5 |
| External independent reproductions — 0 reports, no v1.4 challenge | High | PR 6 |
| LLM advisory — simulation mode (low priority, bundled in PR 6) | Low | PR 6 |

---

## PR sequence

| # | Branch | Title | Gap |
|---|---|---|---|
| PR 1 | `docs/aem-evolve-v1-5-roadmap` | docs: add AEM-EVOLVE™ v1.5 roadmap | Meta |
| PR 2 | `feat/aem-evolve-v1-5-hsm-signing-provider` | feat: add PKCS#11 and KMS signing provider stubs | HSM signing |
| PR 3 | `feat/aem-evolve-v1-5-oidc-hitl-identity` | feat: add OIDC JWT HITL identity verifier | Enterprise IAM |
| PR 4 | `feat/aem-evolve-v1-5-dependency-validation` | feat: add runtime dependency validator | Missing deps |
| PR 5 | `feat/aem-evolve-v1-5-async-postgres-concurrency` | feat: add async concurrency test + pgbouncer guide | Async load |
| PR 6 | `feat/aem-evolve-v1-5-ci-reproduction` | feat: add v1.4 challenge + 16-check verifier | Reproduction |
| PR 7 | `docs/aem-evolve-v1-5-whitepaper` | docs: add AEM-EVOLVE™ v1.5 whitepaper | — |

---

## PR 2 — PKCS#11 and KMS Signing Provider Stubs

**Branch:** `feat/aem-evolve-v1-5-hsm-signing-provider`
**Files:**
- `tools/signing/pkcs11_signing_provider.py` — PKCS#11 provider (requires `pkcs11` library)
- `tools/signing/kms_signing_provider.py` — AWS KMS stub (requires `boto3`)
- `tools/signing/verify_hsm_signing_providers.py` — ABC compliance + graceful-fallback verifier
- `assurance/evolve-multi-agent/v1_5/hsm_signing_report.json`

**Behaviour:** Both providers implement `SigningProvider` ABC. If the required library is not installed, raise `ImportError` with a clear installation message. Verifier confirms ABC shape, import error quality, and that a software-backed provider can substitute.
**Non-claims:** Not a real HSM integration. Requires actual PKCS#11 token or AWS KMS credentials for production use.
**Expected output:** `HSM_SIGNING_VERIFICATION=PASS`

---

## PR 3 — OIDC JWT HITL Identity Verifier

**Branch:** `feat/aem-evolve-v1-5-oidc-hitl-identity`
**Files:**
- `tools/hitl/HITL_OIDC_POLICY.json` — OIDC provider config (issuer, audience, JWKS URI)
- `tools/hitl/oidc_hitl_identity_verifier.py` — RS256 JWT verification against inline JWKS
- `tools/hitl/oidc_token_generator.py` — generates signed RS256 JWTs for CI (no IdP required)
- `assurance/evolve-multi-agent/v1_5/oidc_hitl_report.json`

**Token format:** Standard OIDC ID token (RS256 JWT) with claims: `iss`, `aud`, `sub` (approver_id), `iat`, `exp`, `event_id`.
**JWT implementation:** Uses `cryptography` (already installed) — no PyJWT dependency.
**Non-claims:** Not a real IdP. CI JWKS is generated locally. Production requires external OIDC provider (Okta, Auth0, Keycloak, Azure AD).
**Expected output:** `OIDC_HITL_VERIFICATION=PASS`

---

## PR 4 — Runtime Dependency Validator

**Branch:** `feat/aem-evolve-v1-5-dependency-validation`
**Files:**
- `tools/runtime/dependency_validator.py` — validates all required + optional packages, reports versions
- `tools/runtime/server_smoke_test.py` — imports `main.py` and checks startup health
- `assurance/evolve-multi-agent/v1_5/dependency_validation_report.json`

**Behaviour:** Classifies packages as REQUIRED / OPTIONAL. Required packages failing causes FAIL. Optional packages missing causes WARN. Reports clearly which packages need `pip install`.
**Expected output:** `DEPENDENCY_VALIDATION=PASS`

---

## PR 5 — AsyncPostgresAdapter Concurrency Test + pgbouncer Guide

**Branch:** `feat/aem-evolve-v1-5-async-postgres-concurrency`
**Files:**
- `tools/db/async_postgres_concurrency_test.py` — asyncio concurrent mock test (N concurrent writers)
- `docs/PGBOUNCER_INTEGRATION_GUIDE.md` — pgbouncer config for production async workloads
- `assurance/evolve-multi-agent/v1_5/async_postgres_concurrency_report.json`

**Test design:** Uses `_MockPool` from the mock integration test but fires N concurrent `asyncio.gather()` tasks. Validates no data races on the mock adapter.
**Expected output:** `ASYNC_POSTGRES_CONCURRENCY=PASS`

---

## PR 6 — v1.4 Reproduction Challenge + 16-Check Verifier

**Branch:** `feat/aem-evolve-v1-5-ci-reproduction`
**Files:**
- `challenge/independent-reproduction/AEM_V1_4_INDEPENDENT_REPRODUCTION_CHALLENGE.md`
- `tools/reproduction/verify_all_v1_5.py` — 16-check full-stack verifier (adds v1.5 checks)
- `assurance/evolve-multi-agent/v1_5/REPRODUCTION_REPORT.json`

**Expected output:** `FULL_STACK_VERIFICATION=PASS (16/16)`

---

## PR 7 — Whitepaper v1.5

**Branch:** `docs/aem-evolve-v1-5-whitepaper`
**Files:** `docs/whitepapers/WHITEPAPER_V1_5_AEM_EVOLVE_ENTERPRISE_HARDENING.md`

---

## Non-claims (v1.5 transversal)

```
PKCS#11 provider is not a real HSM integration.
KMS provider is not a real AWS KMS integration.
OIDC verifier is not a real enterprise IdP.
CI JWKS is locally generated, not from a production OIDC provider.
AsyncPostgresAdapter concurrency test uses mocks, not a live database.
External independent reproductions remain at 0 received.
This release is not regulatory approval.
This release is not external certification.
```
