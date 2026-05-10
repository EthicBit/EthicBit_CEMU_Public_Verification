# Public Status Bulletin — AEM-EVOLVE™ v1.8.0

**Date:** 2026-05-09  
**Version:** v1.8.0  
**Status:** READY  
**Full-stack verification:** `FULL_STACK_VERIFICATION=PASS (24/24)`

---

## What shipped

AEM-EVOLVE™ v1.8.0 adds three production hardening features:

**1. OIDC dual-path HITL** — The `/approve` endpoint now accepts OIDC RS256 JWTs in addition to the existing HMAC hex tokens. Format is auto-detected. All prior HMAC integrations remain valid without changes. The JWKS endpoint (`GET /oidc/jwks`) exposes the RS256 public key. Wrong sub, wrong event_id, unregistered sub, and token replay all return 403/409 as expected.

**2. DB adapter switch** — Setting `AEM_DB_ADAPTER=postgres` with a valid `AEM_DB_URL` routes audit tables through `PostgresAdapter`. Default is SQLiteAdapter. Unreachable PostgreSQL falls back to SQLiteAdapter with a warning. LangGraph checkpointing always uses SQLite.

**3. Expanded test suite** — 109 pytest tests now cover key persistence, OIDC dual-path flows, DB adapter labeling, read-time signature verification, replay mitigation, and all prior governance controls.

## Verification

```
FULL_STACK_VERIFICATION=PASS  (24/24)

v1.1: 6/6  ·  v1.2: 2/2  ·  v1.3: 4/4  ·  v1.4: 2/2
v1.5: 2/2  ·  v1.6: 2/2  ·  v1.7: 3/3  ·  v1.8: 3/3
```

Component verifiers:
- `OIDC_WIRED_VERIFICATION=PASS (10/10)`
- `DB_ADAPTER_SWITCH_VERIFICATION=PASS (10/10)`
- pytest suite: `109 passed`

## Non-claims

```
OIDC key pair is locally generated — not a real IdP.
JWKS is served in-process — not a real OIDC provider endpoint.
PostgreSQL not tested against a live database in the verifier.
File-based signing key is not HSM-backed.
HITL secret is a shared HMAC key — not enterprise IAM.
SQLiteAdapter is not production audit storage.
External independent reproductions: 0 received.
Not regulatory approval. Not external certification.
```
