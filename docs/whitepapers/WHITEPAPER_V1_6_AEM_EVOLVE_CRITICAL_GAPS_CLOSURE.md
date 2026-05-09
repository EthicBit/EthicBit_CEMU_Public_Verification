# AEM-EVOLVE™ v1.6.0 — Critical Gaps Closure

**Date:** 2026-05-09
**Tag:** `v1.6.0`
**Base:** v1.5.0 Enterprise Hardening
**Full-stack verification:** `FULL_STACK_VERIFICATION=PASS (18/18)`

---

## 1. Overview

AEM-EVOLVE™ v1.6.0 closes the five critical gaps identified in the v1.5.0 independent audit. Prior releases established signing provider classes, HITL identity verifiers, and a database adapter interface — but none were connected to the running API server. v1.6.0 closes that integration gap.

---

## 2. Gaps closed

### 2.1 Signing provider wired (PR #133)

**Gap:** `EnvSigningProvider`, `Pkcs11SigningProvider`, `KmsSigningProvider` were defined but never instantiated or called from `main.py`. Events and receipts stored `signature_status = "NOT_SIGNED_DEMO"` as a hardcoded string.

**Closure:** `_init_signing_provider()` runs at module load time. It tries `EnvSigningProvider` (reads `ETHICBIT_ED25519_PRIVATE_KEY_PEM`); on failure it generates an ephemeral Ed25519 key. `_signing_provider` and `_SIGNING_STATUS` are module-level singletons.

Every call to `create_evolution_event()` now:
1. Computes `event_canonical_sha256 = SHA256(canonical_json(event))`
2. Signs it: `signature_hex = provider.sign(sha256.encode()).hex()`
3. Attaches `signature_hex`, `signature_algorithm`, `signature_status` to the event dict and to the DB row

The same pattern applies to `evaluate_evolution_gate()` for receipts.

**Verification:** `verify_signed_receipts.py` — 10 checks including cryptographic `verify()` round-trip. `SIGNED_RECEIPTS_VERIFICATION=PASS (10/10)`

### 2.2 HITL identity enforced in /approve (PR #133)

**Gap:** `/approve` derived `approver_id` from the API key, not from a verified identity token. `ApproveRequest` had no token field. HMAC and OIDC verifiers were standalone scripts never called by the server.

**Closure:**

```python
class ApproveRequest(BaseModel):
    thread_id: str
    decision: Literal["approve", "reject"]
    override_reason: Optional[str] = None
    hitl_token: Optional[str] = None        # NEW
    hitl_approver_id: Optional[str] = None  # NEW
```

When `human_approval_needed` is `True`, `/approve` requires both fields. Missing → 400. Token validated by `_verify_hitl_token()` → `hitl_identity_verifier.verify_token()`. Invalid → 403. `approver_id` is sourced from the verified token, not the API key.

**Verification:** `e2e_api_test.py` C-05 (missing token → 400), C-06 (invalid token → 403), C-07 (valid token → 200).

### 2.3 SQLiteAdapter activated (PR #133)

**Gap:** `db_adapter.py` defined `SQLiteAdapter`, `PostgresAdapter`, `AsyncPostgresAdapter` but `main.py` called `sqlite3.connect()` directly. The adapter interface was unreachable from any production code path.

**Closure:** `build_graph()` now instantiates `SQLiteAdapter(DEMO_DB_PATH)`. All audit functions (`init_audit_tables`, `_append_audit_chain`, `create_evolution_event`, `evaluate_evolution_gate`) and all endpoint handlers use `adapter.execute()`, `adapter.execute_write()`, `adapter.commit()`. LangGraph's `SqliteSaver` receives a dedicated raw `sqlite3.Connection` to avoid threading contention.

### 2.4 Health endpoint false claim fixed (PR #133)

**Gap:** `/health` hardcoded `"signature_status": "DEMO_SIGNED_ED25519"` regardless of whether signing was actually working.

**Closure:** Both `/health` and `/healthz` now return `_SIGNING_STATUS`, which reflects actual runtime state (`SIGNED_Ed25519_ENV` or `SIGNED_EPHEMERAL_Ed25519`).

### 2.5 CI and E2E integration test (PR #134)

**Gap:** `aem-evolve-reproduction.yml` ran only v1.3/v1.4 unit verifiers. No test started the server, made HTTP requests, or validated the end-to-end governance flow.

**Closure:**
- `tools/integration/e2e_api_test.py` — 10-check TestClient test: `POST /start` → `GET /status` → `GET /receipt` → `POST /approve` (with HITL token) → `GET /audit` → `GET /chain/verify`. Validates signed artifacts throughout.
- `tools/reproduction/verify_all_v1_6.py` — 18-check full-stack verifier including `V1_6-SIGNED-RECEIPTS` and `V1_6-E2E-API`.
- `aem-evolve-reproduction.yml` updated to run v1.3, v1.4, v1.5, v1.6 verifiers plus the E2E test.

---

## 3. Full-stack verification

```
FULL_STACK_VERIFICATION=PASS  (18/18)
  v1.1: 6/6  ·  v1.2: 2/2  ·  v1.3: 4/4  ·  v1.4: 2/2  ·  v1.5: 2/2  ·  v1.6: 2/2

  V1_6-SIGNED-RECEIPTS    SIGNED_RECEIPTS_VERIFICATION=PASS (10/10)
  V1_6-E2E-API            E2E_API_VERIFICATION=PASS (10/10)
```

```bash
pip install cryptography mlkem asyncpg fastapi langgraph starlette httpx
python3 demos/aem-evolve-multi-agent-api/tools/reproduction/verify_all_v1_6.py
```

---

## 4. Non-claims (transversal v1.6)

```
PKCS#11 provider is not a real HSM integration.
KMS provider is not a real AWS KMS integration.
OIDC verifier uses locally generated JWKS — not a real IdP.
Ephemeral signing key is not persisted across server restarts.
HITL enforcement uses HMAC shared secret — not enterprise IAM.
SQLiteAdapter is demo storage — not production audit storage.
External independent reproductions remain at 0 received.
This release is not regulatory approval.
This release is not external certification.
```

---

## 5. Remaining gaps (post v1.6 audit)

| Gap | Status | Path to closure |
|---|---|---|
| Ephemeral signing key | Known non-claim | Set `ETHICBIT_ED25519_PRIVATE_KEY_PEM` to persist across restarts |
| OIDC not wired into /approve | Open | Add OIDC token validation path alongside HMAC |
| PostgreSQL adapter unused | Open | Set `AEM_DB_URL` + switch `build_graph()` to `PostgresAdapter` |
| LangGraph off path for advisory | Advisory only by design | Add `/advisory` endpoint for on-demand Claude invocation |
| ML-KEM768 not in governance | Post-quantum roadmap | Add KEM key exchange to session establishment |
