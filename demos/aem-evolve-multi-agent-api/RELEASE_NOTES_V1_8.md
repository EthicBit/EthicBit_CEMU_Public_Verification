# Release Notes — AEM-EVOLVE™ v1.8.0

**Date:** 2026-05-09  
**Tag:** `v1.8.0`  
**Type:** Production hardening — OIDC dual-path HITL · PostgreSQL adapter switch · Fast-path pytest suite

---

## Summary

v1.8.0 closes three production hardening gaps identified in the v1.7.0 post-release audit:

1. **OIDC dual-path HITL** — `/approve` now accepts both OIDC RS256 JWTs and HMAC hex tokens. Token format is auto-detected by dot count (`token.count(".") == 2`). Backwards-compatible: all existing HMAC integrations work unchanged.
2. **DB adapter switch** — `AEM_DB_ADAPTER` env var selects `sqlite` (default) or `postgres`. When `postgres` is selected, `AEM_DB_URL` is required; missing or unreachable URLs fall back to SQLiteAdapter with a warning. LangGraph SqliteSaver always stays on SQLite.
3. **Fast-path pytest suite** — 109 tests across four test files covering key persistence, OIDC dual-path, DB adapter label, and all prior governance controls.

**Full-stack verification:** `FULL_STACK_VERIFICATION=PASS (24/24)`

---

## Changes

### `main.py`

- Version bumped to `0.6.0-demo`
- `_oidc_key_pair: object | None` and `_OIDC_POLICY: dict` — module-level OIDC state
- `_init_oidc_provider()` — loads `HITL_OIDC_POLICY.json`, generates ephemeral RSA-2048 key pair at startup
- `_verify_hitl_token_oidc()` — validates JWT signature (RS256), `sub` matches `hitl_approver_id`, `event_id` claim matches, sub is in `approver_registry`, token not replayed
- `_verify_hitl_token()` — dot-count detection: JWT path → OIDC verifier; hex path → HMAC verifier
- `_build_db_adapter()` — reads env vars, returns `(adapter, label)` tuple; falls back to SQLiteAdapter
- `build_graph()` — returns `(graph, db_adapter, adapter_label)` triple
- `GET /oidc/jwks` — serves ephemeral RSA public key as JWKS (RS256, kid `demo-key-1`)
- `/health` — adds `hitl_identity_enforcement`, `hitl_oidc_path`, `db_adapter`, `db_adapter_switch` fields
- `/healthz` — `db` field reflects active adapter type (`sqlite` or `postgres`)

### New test files

- `tests/test_signing_controls.py` — `TestKeyPersistence` (8 tests), `TestDbAdapterLabel` (2 tests)
- `tests/test_oidc_hitl.py` — `TestOIDCProviderInit` (4 tests), `TestOIDCApproval` (6 tests)

### New verifier scripts

- `tools/hitl/verify_oidc_wired.py` — 10 checks: `OIDC_WIRED_VERIFICATION=PASS (10/10)`
- `tools/db/verify_db_adapter_switch.py` — 10 checks: `DB_ADAPTER_SWITCH_VERIFICATION=PASS (10/10)`
- `tools/reproduction/verify_all_v1_8.py` — 24-check full-stack verifier

### Assurance artifacts

- `assurance/evolve-multi-agent/v1_8/oidc_wired_report.json`
- `assurance/evolve-multi-agent/v1_8/db_adapter_switch_report.json`
- `assurance/evolve-multi-agent/v1_8/REPRODUCTION_REPORT.json`

---

## Non-claims

```
OIDC key pair is locally generated — not a real IdP.
JWKS is served in-process — not a real OIDC provider endpoint.
Production requires external OIDC provider (Okta, Auth0, Keycloak).
PostgreSQL path not tested with a live database in this verifier.
Connection pool sizing is demo-grade.
File-based signing key is not HSM-backed key custody.
HITL enforcement uses HMAC shared secret — not enterprise IAM.
SQLiteAdapter is demo storage — not production audit storage.
External independent reproductions remain at 0 received.
This release is not regulatory approval.
This release is not external certification.
```
