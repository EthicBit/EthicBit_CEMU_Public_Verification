# AEM-EVOLVE™ Multi-Agent Governance API — Release Notes v1.5.0

**Release date:** 2026-05-09
**Git tag:** `v1.5.0`
**Branch:** `main`
**Base:** v1.4.0 — Production Hardening
**Commit SHA:** `8297a0c1`

---

## What is v1.5.0?

v1.5.0 closes all six enterprise hardening gaps identified in the v1.4.0 audit. It introduces PKCS#11/KMS signing provider stubs, OIDC RS256 JWT HITL identity verification, a runtime dependency validator, an async concurrency test with pgbouncer guide, and a v1.4 reproduction challenge.

---

## Verification results

```
FULL_STACK_VERIFICATION=PASS  (16/16)
  v1.1: 6/6  ·  v1.2: 2/2  ·  v1.3: 4/4  ·  v1.4: 2/2  ·  v1.5: 2/2
```

```bash
python3 demos/aem-evolve-multi-agent-api/tools/reproduction/verify_all_v1_5.py
```

---

## Non-claims (transversal v1.5)

```
PKCS#11 provider is not a real HSM integration.
KMS provider is not a real AWS KMS integration.
OIDC verifier uses locally generated JWKS — not a real IdP.
AsyncPostgresAdapter concurrency test uses mocks, not a live database.
External independent reproductions remain at 0 received.
This release is not regulatory approval.
This release is not external certification.
```
