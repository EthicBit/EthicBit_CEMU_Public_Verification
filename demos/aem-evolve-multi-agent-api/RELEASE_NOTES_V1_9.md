# Release Notes — AEM-EVOLVE™ v1.9.0

**Date:** 2026-05-10  
**Tag:** `v1.9.0`  
**Type:** Production hardening — OIDC key persistence · materiality parametrized · Postgres live test

---

## Summary

v1.9.0 closes three technical gaps identified in the v1.8.0 post-release audit, completing the v1.x production-hardening sequence before the v2.0 production-readiness gate.

1. **OIDC key pair persistence** — `oidc_key.pem` replaces ephemeral RSA key. `OidcTestKeyPair.load_or_generate(path)` generates once and reloads on restart. kid is derived deterministically from the public key DER (`SHA256(pub_der)[:8]` base64url-encoded) — stable across restarts.

2. **Materiality parametrized** — `StartRequest.materiality_score: float = 78.0` (0.0–100.0). `writer_agent` reads from state. All three governance paths are now reachable via the API: `FAIL_CLOSED` (>85), `SCOPE_LIMITED` (70–85), `PASS` (≤70).

3. **Postgres live integration test** — `verify_postgres_live.py` runs 10 checks against a real PostgreSQL instance when `AEM_DB_URL` is set. Gracefully SKIPS (counts as PASS) when `AEM_DB_URL` is absent, making it safe for environments without a live DB. Pytest counterpart in `tests/test_postgres_live.py`.

**Full-stack verification:** `FULL_STACK_VERIFICATION=PASS (27/27)`  
**Pytest suite:** `129 passed, 9 skipped`

---

## Changes

### `tools/hitl/oidc_token_generator.py`
- `OidcTestKeyPair.load_or_generate(pem_path)` classmethod added
- kid derived deterministically: `base64url(SHA256(pub_der)[:8])`

### `main.py`
- `_OIDC_KEY_FILE_NAME = "oidc_key.pem"` constant added
- `_init_oidc_provider()` calls `OidcTestKeyPair.load_or_generate(key_file)` — persists to `oidc_key.pem`
- `StartRequest.materiality_score: float = 78.0` — validated 0.0–100.0
- `writer_agent` reads `state.get("materiality_score", 78.0)` instead of hardcoded 78.0
- `start_session` passes `materiality_score` into initial state
- `/health` adds `oidc_key_persistence`, `materiality_parametrized`, `governance_paths`
- Version bumped to `0.7.0-demo`

### New test files
- `tests/test_oidc_key_persistence.py` — 10 tests: file exists, RSA, 2048 bits, deterministic kid, cross-reload verify, health field
- `tests/test_materiality_paths.py` — 11 tests: all 3 paths, receipt outcomes, validation errors, health fields
- `tests/test_postgres_live.py` — 9 tests (skipped if no `AEM_DB_URL`)

### New verifier scripts
- `tools/signing/verify_oidc_key_persistence.py` — 10 checks: `OIDC_KEY_PERSISTENCE_VERIFICATION=PASS (10/10)`
- `tools/governance/verify_materiality_paths.py` — 10 checks: `MATERIALITY_PATHS_VERIFICATION=PASS (10/10)`
- `tools/db/verify_postgres_live.py` — 10 checks: `POSTGRES_LIVE_VERIFICATION=PASS` (SKIP if no AEM_DB_URL)
- `tools/reproduction/verify_all_v1_9.py` — 27-check full-stack verifier

### Assurance artifacts
- `assurance/evolve-multi-agent/v1_9/oidc_key_persistence_report.json`
- `assurance/evolve-multi-agent/v1_9/materiality_paths_report.json`
- `assurance/evolve-multi-agent/v1_9/postgres_live_report.json`
- `assurance/evolve-multi-agent/v1_9/REPRODUCTION_REPORT.json`

---

## Non-claims

```
OIDC key file is not HSM-backed key custody.
Key stored unencrypted on disk — not enterprise key management.
PostgreSQL live test requires AEM_DB_URL — SKIPPED if not set.
Materiality score is caller-supplied — not externally audited.
HITL enforcement uses HMAC shared secret — not enterprise IAM.
SQLiteAdapter is demo storage — not production audit storage.
External independent reproductions remain at 0 received.
This release is not regulatory approval.
This release is not external certification.
v1.9 closes the v1.x hardening sequence — v2.0 gate is required for production-readiness evidence.
```
