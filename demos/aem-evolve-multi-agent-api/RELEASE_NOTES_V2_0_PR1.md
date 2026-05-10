# Release Notes — AEM-EVOLVE™ v2.0 PR 1

**Date:** 2026-05-10  
**Tag:** `v2.0-pr1`  
**Type:** v2.0 gate — Production OIDC provider enforcement layer  
**Version:** `0.8.0-demo`

---

## Summary

PR 1 installs the production OIDC integration layer required by the v2.0 Production
Readiness Gate. When `OIDC_ISSUER` is configured, the server uses an external OIDC
provider (Okta, Auth0, Azure AD, Keycloak) for HITL token verification instead of the
local demo RSA key pair. When `OIDC_ISSUER` is not configured, the server falls back
to the v1.9 demo path — the gate honestly reports `PRODUCTION_OIDC_PROVIDER_CHECK=FAIL`.

**Gate result (local/demo environment):** `PRODUCTION_OIDC_PROVIDER_CHECK=FAIL`  
*Expected — gate requires a real external IdP.*

**Test suite:** `144 passed, 10 skipped`

---

## Changes

### `security/__init__.py` (new)
Package marker.

### `security/oidc_config.py` (new)
- `ProductionOidcConfig` frozen dataclass: `issuer`, `jwks_uri`, `audience`, `jwks_ttl_seconds`
- `load_oidc_config()` reads `OIDC_ISSUER`, `OIDC_JWKS_URI`, `OIDC_AUDIENCE`, `OIDC_JWKS_TTL_SECONDS`
- Returns `None` when `OIDC_ISSUER` is not set

### `security/oidc_provider.py` (new)
- `ProductionOidcProvider` — external OIDC integration
- `from_env()` classmethod — returns `None` when `OIDC_ISSUER` not set
- `fetch_jwks()` — TTL-cached HTTPS fetch from `OIDC_JWKS_URI`
- `verify_token()` — RS256 validation: signature, issuer, audience, expiry
- `gate_check()` — structured gate status dict for `/health` and assurance

### `main.py` (modified)
- `_production_oidc_provider` module-level singleton (v2.0 PR 1 production path)
- `_init_oidc_provider()` tries production path first, falls back to demo path
- `_verify_hitl_token_oidc()` routes to production provider when configured
- `/health` adds `hitl_oidc_mode` (`PRODUCTION` | `DEMO`) and `production_oidc_gate`
- Version bumped to `0.8.0-demo`

### `tests/test_oidc_provider_enforcement.py` (new)
- `TestOidcConfig` — 8 tests: config loading, env var behavior, frozen dataclass
- `TestProductionOidcProviderInit` — 5 tests: from_env, gate_check, verify_token
- `TestHealthOidcGate` — 3 tests (2 skipped when OIDC_ISSUER not set)
- **15 passed, 1 skipped** in isolation

### `tools/production_readiness/verify_oidc_provider.py` (new)
- 10-check gate verifier
- C-01: OIDC_ISSUER configured (FAIL in demo — correct)
- C-02: security.oidc_config importable
- C-03: security.oidc_provider importable
- C-04: load_oidc_config returns None when unset
- C-05: from_env() mirrors config result
- C-06–C-10: provider validation (skipped when no issuer)
- Emits assurance report to `assurance/evolve-multi-agent/v2_0/oidc_provider_check_report.json`

### `docs/OIDC_PROVIDER_ENFORCEMENT.md` (new)
Feature specification and gate configuration guide.

### Assurance artifact
- `assurance/evolve-multi-agent/v2_0/oidc_provider_check_report.json`

---

## Gate result (assurance artifact)

```json
{
  "gate": "PRODUCTION_OIDC_PROVIDER_CHECK",
  "result": "FAIL",
  "fail_reason": "OIDC_ISSUER not configured — external OIDC provider required"
}
```

`FAIL` is the honest and correct result for a local/demo environment.

---

## Non-claims

```
PRODUCTION_OIDC_PROVIDER_CHECK=FAIL — gate not satisfied in local/demo environment.
This PR does not certify the external OIDC provider.
This PR does not grant regulatory approval.
This PR does not replace external IAM certification.
This PR is not production-ready by itself.
PASS requires a real external OIDC provider — not a demo key pair.
This release is not regulatory approval.
This release is not external certification.
```
