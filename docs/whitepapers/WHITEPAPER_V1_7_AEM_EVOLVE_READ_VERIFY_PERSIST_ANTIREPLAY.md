# AEM-EVOLVE™ v1.7.0 — Read-Time Verification, Key Persistence, Anti-Replay

**Date:** 2026-05-10
**Tag:** `v1.7.0`
**Base:** v1.6.0 Critical Gaps Closure
**Full-stack verification:** `FULL_STACK_VERIFICATION=PASS (21/21)`

---

## 1. Overview

AEM-EVOLVE™ v1.7.0 closes the three critical gaps identified in the v1.6.0 post-release audit. v1.6.0 wired Ed25519 signing into all write paths but left three exploitable weaknesses: artifacts were signed at write time but not verified at read time; the signing key was regenerated on every restart (ephemeral); and HITL tokens were valid for the full 10-minute TTL window with no nonce enforcement, enabling replay attacks.

---

## 2. Gaps closed

### 2.1 Read-time signature verification (gap 1)

**Gap:** `GET /receipt`, `GET /event`, `GET /audit` returned signed artifacts without calling `provider.verify()`. A caller could not distinguish a valid signature from a tampered one by inspecting the response alone.

**Closure:** `_verify_artifact_signature(artifact: dict) -> dict` is called on every artifact before it is returned:

1. Determines the canonical SHA key: `receipt_canonical_sha256` if present (receipts), else `event_canonical_sha256` (events).
2. Calls `_signing_provider.verify(canonical_sha256.encode(), bytes.fromhex(signature_hex))`.
3. Adds `signature_verified: bool` and `signature_verification_note: str` to the returned artifact.

A tampered `signature_hex` returns `signature_verified: false, signature_verification_note: "signature_invalid"`. Missing fields return `signature_verified: false, signature_verification_note: "missing_signature_fields"`.

**Verification:** `verify_read_time_signatures.py` — 10 checks including tamper detection and endpoint coverage. `READ_TIME_SIG_VERIFICATION=PASS (10/10)`

### 2.2 Key persistence (gap 2)

**Gap:** `_init_signing_provider()` fell back to generating an ephemeral `Ed25519PrivateKey` in memory. Every server restart produced a new key, invalidating all previously issued signatures.

**Closure:** `_init_signing_provider()` now follows a three-step priority chain:

1. `EnvSigningProvider` — reads `ETHICBIT_ED25519_PRIVATE_KEY_PEM` (unchanged).
2. `FileSigningProvider(DEMO_ROOT / "signing_key.pem")` — loads persistent key if file exists.
3. Generate a new `Ed25519PrivateKey` → write PEM to `signing_key.pem` → load via `FileSigningProvider`.

`_SIGNING_STATUS` is now `"SIGNED_Ed25519_FILE"` for paths 2 and 3, replacing `"SIGNED_EPHEMERAL_Ed25519"`. The key survives restarts. `/health` reflects `"key_persistence": "FILE_BASED"`.

**Verification:** `verify_key_persistence.py` — 10 checks including PEM validity, two-load public key identity, and sign/verify round-trip. `KEY_PERSISTENCE_VERIFICATION=PASS (10/10)`

### 2.3 Replay attack mitigation (gap 3)

**Gap:** HITL tokens were valid for the full TTL window (10 minutes). The same token could be submitted multiple times to `/approve` within that window. No nonce or one-time-use enforcement existed.

**Closure:**

`hitl_used_tokens` table added to `init_audit_tables()`:
```sql
CREATE TABLE IF NOT EXISTS hitl_used_tokens (
    token_hash TEXT NOT NULL,
    event_id TEXT NOT NULL,
    approver_id TEXT NOT NULL,
    used_at TEXT NOT NULL,
    PRIMARY KEY (token_hash, event_id)
)
```

`_is_token_used(token, event_id, adapter)` queries by `SHA256(token)` and `event_id`.
`_mark_token_used(token, event_id, approver_id, adapter)` inserts on first use; idempotent via `INSERT OR IGNORE`.

In `/approve`, after successful HITL token verification:
1. `_is_token_used(token, event_id, adapter)` — if `True` → HTTP 409 "replay detected".
2. `_mark_token_used(...)` — persists nonce before processing the decision.

**Verification:** `verify_replay_mitigation.py` — 10 checks including table existence, idempotency, 409 response, and body content. `REPLAY_MITIGATION_VERIFICATION=PASS (10/10)`

---

## 3. Full-stack verification

```
FULL_STACK_VERIFICATION=PASS  (21/21)
  v1.1: 6/6  ·  v1.2: 2/2  ·  v1.3: 4/4  ·  v1.4: 2/2  ·  v1.5: 2/2  ·  v1.6: 2/2  ·  v1.7: 3/3

  V1_7-READ-TIME-SIG       READ_TIME_SIG_VERIFICATION=PASS (10/10)
  V1_7-REPLAY-MITIGATION   REPLAY_MITIGATION_VERIFICATION=PASS (10/10)
  V1_7-KEY-PERSISTENCE     KEY_PERSISTENCE_VERIFICATION=PASS (10/10)
  V1_6-E2E-API             E2E_API_VERIFICATION=PASS (14/14)
```

```bash
pip install cryptography mlkem asyncpg fastapi langgraph starlette httpx
python3 demos/aem-evolve-multi-agent-api/tools/reproduction/verify_all_v1_7.py
```

---

## 4. Non-claims (transversal v1.7)

```
File-based signing key is not HSM-backed key custody.
Key stored unencrypted on disk — not enterprise key management.
Replay nonce store is SQLite-backed — not tamper-proof.
PKCS#11 provider is not a real HSM integration.
KMS provider is not a real AWS KMS integration.
OIDC verifier uses locally generated JWKS — not a real IdP.
HITL enforcement uses HMAC shared secret — not enterprise IAM.
SQLiteAdapter is demo storage — not production audit storage.
External independent reproductions remain at 0 received.
This release is not regulatory approval.
This release is not external certification.
```

---

## 5. Remaining gaps (post v1.7 audit)

| Gap | Status | Path to closure |
|---|---|---|
| File key unencrypted on disk | Known non-claim | Set `ETHICBIT_ED25519_PRIVATE_KEY_PEM` or use HSM |
| Replay nonce store not tamper-proof | Known non-claim | Requires tamper-evident DB (PostgreSQL + audit log) |
| OIDC not wired into /approve | Open | Add OIDC token validation path alongside HMAC |
| PostgreSQL adapter not active | Open | Set `AEM_DB_URL` + switch `build_graph()` to `PostgresAdapter` |
| ML-KEM768 not in governance path | Post-quantum roadmap | Add KEM key exchange to session establishment |
