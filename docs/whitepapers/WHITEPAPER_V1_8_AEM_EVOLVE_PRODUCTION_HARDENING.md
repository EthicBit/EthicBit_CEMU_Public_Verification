# AEM-EVOLVE™ v1.8.0 — Production Hardening: OIDC HITL · DB Adapter Switch · Expanded Test Suite

**Date:** 2026-05-09  
**Version:** v1.8.0  
**Authors:** EthicBit Engineering  
**Classification:** Public — Reproducible Demo

---

## Abstract

AEM-EVOLVE™ v1.8.0 delivers three production hardening measures identified in the v1.7.0 post-release audit: (1) a dual-path HITL approval mechanism that accepts both OIDC RS256 JWTs and legacy HMAC hex tokens without breaking backwards compatibility; (2) an environment-variable-driven database adapter switch enabling PostgreSQL as the audit store alongside the default SQLiteAdapter; (3) a 109-test fast-path pytest suite covering key persistence, OIDC approval flows, DB adapter labeling, and all prior governance controls. Full-stack verification: `FULL_STACK_VERIFICATION=PASS (24/24)`.

---

## 1. Motivation

The v1.7.0 audit identified three hardening gaps:

| Gap | Risk | v1.8.0 closure |
|---|---|---|
| HITL only supported HMAC shared secret | No path to real IAM integration | OIDC dual-path: JWT → RS256 verify; hex → HMAC verify |
| DB adapter hardcoded to SQLite | No path to production audit store | `AEM_DB_ADAPTER` env var; `_build_db_adapter()` factory |
| Governance tests lived only in verifier scripts | Slower developer feedback loop | 109-test pytest suite in `tests/` |

---

## 2. OIDC Dual-Path HITL

### 2.1 Design

The `/approve` endpoint accepts a `hitl_token` field that may contain either:
- An **OIDC JWT** — three dot-separated Base64URL segments (header.payload.signature)
- An **HMAC hex** — 64-character hexadecimal string (SHA-256 HMAC)

Auto-detection uses `token.count(".") == 2` as the discriminator. This avoids a breaking API change: existing clients sending HMAC tokens continue to work without modification.

### 2.2 OIDC Verification Steps

For the JWT path, `_verify_hitl_token_oidc()` enforces:

1. **Signature** — RS256 verify against the module-level `_oidc_key_pair.public_key`
2. **Sub matches** — JWT `sub` claim must equal `hitl_approver_id` in the request body
3. **Event binding** — JWT `event_id` claim must equal the `event_id` on the pending thread
4. **Approver registry** — `sub` must appear in `_OIDC_POLICY["approver_registry"]`
5. **Replay prevention** — token SHA-256 hash must not exist in `hitl_used_tokens` table

### 2.3 JWKS Endpoint

`GET /oidc/jwks` returns the ephemeral RSA-2048 public key as a JWKS document with `alg=RS256` and `kid=demo-key-1`. In production, this would be replaced by an external OIDC provider's JWKS URI.

### 2.4 Health Reporting

`GET /health` now includes:
```json
{
  "hitl_identity_enforcement": "HMAC_AND_OIDC_DUAL_PATH",
  "hitl_oidc_path": "ENABLED"
}
```

### 2.5 Verification

`OIDC_WIRED_VERIFICATION=PASS (10/10)` — checks: key pair initialized, policy loaded, JWKS RS256, OIDC approve → 200, HMAC still → 200, wrong sub → 403, wrong event_id → 403, unregistered sub → 403, replay → 409, health shows ENABLED.

---

## 3. Database Adapter Switch

### 3.1 Design

`_build_db_adapter()` reads two environment variables at startup:

| Var | Default | Effect |
|---|---|---|
| `AEM_DB_ADAPTER` | `sqlite` | Selects adapter type |
| `AEM_DB_URL` | (none) | PostgreSQL DSN when adapter=postgres |

Fallback chain:
1. `AEM_DB_ADAPTER=postgres` + `AEM_DB_URL` set → attempt `PostgresAdapter(url)`; on any exception, fall back to SQLiteAdapter with warning
2. `AEM_DB_ADAPTER=postgres` + no `AEM_DB_URL` → immediate SQLiteAdapter fallback
3. Any other value → SQLiteAdapter

`build_graph()` returns `(compiled_graph, db_adapter, adapter_label)`. The module-level assignment `graph, db_adapter, _db_adapter_label = build_graph()` exposes the label for health reporting.

**Note:** LangGraph `SqliteSaver` always uses SQLite for graph checkpointing, regardless of `AEM_DB_ADAPTER`. Only the audit tables (evolution_events, evolution_receipts, human_decisions, audit_chain, hitl_used_tokens) route through the switchable adapter.

### 3.2 Health Reporting

`GET /health` adds:
```json
{
  "db_adapter": "SQLiteAdapter",
  "db_adapter_switch": "AEM_DB_ADAPTER env var (sqlite|postgres) + AEM_DB_URL"
}
```

`GET /healthz` `db` field reflects the active type (`"sqlite"` or `"postgres"`).

### 3.3 Verification

`DB_ADAPTER_SWITCH_VERIFICATION=PASS (10/10)` — checks: importable, default SQLite, explicit sqlite, postgres no-URL fallback, postgres bad-URL fallback, label reflects adapter, health db_adapter field, health db_adapter_switch field, healthz db field, SQLiteAdapter init_audit_tables creates all 5 expected tables.

---

## 4. Expanded Test Suite

### 4.1 Test counts

| File | Tests | Scope |
|---|---|---|
| `tests/test_endpoints.py` | 39 | API endpoints, version, health fields |
| `tests/test_governance_logic.py` | 26 | Read-time verify, replay, HITL logic |
| `tests/test_signing_controls.py` | 10 | Key persistence, DB adapter label |
| `tests/test_oidc_hitl.py` | 10 | OIDC provider init, dual-path approval |
| **Total** | **109** | |

### 4.2 Key new tests

`TestKeyPersistence` — verifies `signing_key.pem` exists, is valid Ed25519, status is `SIGNED_Ed25519_FILE`, sign returns 64 bytes, verify roundtrip succeeds, tampered signature fails verification, algorithm is Ed25519, public_key_pem is not empty.

`TestOIDCApproval` — verifies OIDC JWT → 200, HMAC → 200, wrong sub → 403, wrong event_id → 403, replay → 409, unregistered sub → 403.

---

## 5. Full-Stack Verification

```
FULL_STACK_VERIFICATION=PASS  (24/24)

v1.1: 6/6  ·  v1.2: 2/2  ·  v1.3: 4/4  ·  v1.4: 2/2  ·
v1.5: 2/2  ·  v1.6: 2/2  ·  v1.7: 3/3  ·  v1.8: 3/3
```

Reproduced by running:
```bash
pip install cryptography mlkem asyncpg fastapi langgraph starlette httpx jose
python3 demos/aem-evolve-multi-agent-api/tools/reproduction/verify_all_v1_8.py
```

---

## 6. Non-Claims

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
