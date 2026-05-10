# AEM-EVOLVE™ v2.0 PR 1 — Production OIDC Provider Enforcement

**Document type:** Feature specification  
**Version:** v2.0 PR 1  
**Date:** 2026-05-10  
**Gate output required:** `PRODUCTION_OIDC_PROVIDER_CHECK=PASS`

---

## What this PR adds

PR 1 installs the production OIDC integration layer on top of the v1.9 demo OIDC path.
When `OIDC_ISSUER` is configured, the server uses an external OIDC provider (Okta, Auth0,
Azure AD, Keycloak) for HITL token verification instead of the local demo RSA key pair.

---

## Architecture — dual-path OIDC

```
OIDC_ISSUER set?
  YES → ProductionOidcProvider (external IdP, JWKS-backed RS256 verification)
  NO  → OidcTestKeyPair demo path (local RSA file key — v1.9 behavior)
```

The production path always takes priority when `OIDC_ISSUER` is configured.

---

## Files added

| File | Purpose |
|---|---|
| `security/__init__.py` | Package marker |
| `security/oidc_config.py` | `ProductionOidcConfig` dataclass + `load_oidc_config()` from env |
| `security/oidc_provider.py` | `ProductionOidcProvider` — JWKS fetch, TTL cache, `verify_token()`, `gate_check()` |
| `tools/production_readiness/verify_oidc_provider.py` | 10-check gate verifier |
| `tests/test_oidc_provider_enforcement.py` | Pytest test suite |
| `docs/OIDC_PROVIDER_ENFORCEMENT.md` | This document |

---

## Environment variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `OIDC_ISSUER` | Yes (for PASS) | — | Issuer URL of external OIDC provider |
| `OIDC_JWKS_URI` | No | `<OIDC_ISSUER>/.well-known/jwks.json` | JWKS endpoint |
| `OIDC_AUDIENCE` | No | `aem-evolve` | Expected JWT audience claim |
| `OIDC_JWKS_TTL_SECONDS` | No | `300` | JWKS cache TTL in seconds |

---

## Gate behavior

The gate **FAILS** when `OIDC_ISSUER` is not configured. This is the correct and
expected outcome for a local or demo environment. The gate cannot PASS without an
external OIDC provider.

To satisfy this gate for a defined target environment:

1. Configure an external OIDC provider (Okta, Auth0, Azure AD, Keycloak)
2. Set `OIDC_ISSUER`, `OIDC_JWKS_URI` (optional), `OIDC_AUDIENCE` (optional)
3. Run the verifier: `python3 tools/production_readiness/verify_oidc_provider.py`
4. Gate must output `PRODUCTION_OIDC_PROVIDER_CHECK=PASS`
5. Satisfy all remaining checklist items from `docs/production/AEM_EVOLVE_V2_0_PRODUCTION_READINESS_GATE_CHECKLIST.md` PR 1 section

---

## Health endpoint fields added

```json
{
  "hitl_oidc_mode": "PRODUCTION | DEMO",
  "production_oidc_gate": {
    "gate": "PRODUCTION_OIDC_PROVIDER_CHECK",
    "status": "PASS | FAIL | NOT_CONFIGURED",
    "issuer": "...",
    "jwks_uri": "...",
    "audience": "...",
    "jwks_reachable": true,
    "jwks_key_count": 2
  }
}
```

---

## Non-claims

```
This PR does not satisfy the PRODUCTION_OIDC_PROVIDER_CHECK gate without an external IdP.
This PR does not certify the external OIDC provider.
This PR does not grant regulatory approval.
This PR does not replace external IAM certification.
This PR is not production-ready by itself.
PASS in the gate verifier requires a real external OIDC provider.
```
