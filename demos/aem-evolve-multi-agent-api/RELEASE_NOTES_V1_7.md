# AEM-EVOLVE™ Multi-Agent Governance API — Release Notes v1.7.0

**Release date:** 2026-05-10
**Git tag:** `v1.7.0`
**Branch:** `main`
**Base:** v1.6.0 — Critical Gaps Closure
**Commit SHA:** TBD

---

## What is v1.7.0?

v1.7.0 closes the three critical gaps identified in the v1.6.0 post-release audit:

1. **Read-time signature verification** — GET /receipt, /event, /audit now call `provider.verify()` and return `signature_verified: true/false` on every artifact.
2. **Key persistence** — the signing key is now persisted to `signing_key.pem` and reloaded across server restarts. Status changes from `SIGNED_EPHEMERAL_Ed25519` → `SIGNED_Ed25519_FILE`.
3. **Replay attack mitigation** — HITL tokens are one-time-use per `(token_hash, event_id)` pair. A second approve with the same token returns 409.

---

## Verification results

```
FULL_STACK_VERIFICATION=PASS  (21/21)
  v1.1: 6/6  ·  v1.2: 2/2  ·  v1.3: 4/4  ·  v1.4: 2/2  ·  v1.5: 2/2  ·  v1.6: 2/2  ·  v1.7: 3/3

  V1_7-READ-TIME-SIG       READ_TIME_SIG_VERIFICATION=PASS (10/10)
  V1_7-REPLAY-MITIGATION   REPLAY_MITIGATION_VERIFICATION=PASS (10/10)
  V1_7-KEY-PERSISTENCE     KEY_PERSISTENCE_VERIFICATION=PASS (10/10)
  V1_6-E2E-API             E2E_API_VERIFICATION=PASS (14/14)
```

```bash
python3 demos/aem-evolve-multi-agent-api/tools/reproduction/verify_all_v1_7.py
```

---

## Gaps closed

| Gap | Closure |
|---|---|
| Read-time signature verification | `_verify_artifact_signature()` called in GET /receipt, /event, /audit; `signature_verified` field returned |
| Key persistence | `signing_key.pem` generated once and reloaded; `SIGNED_Ed25519_FILE` status |
| Replay attack mitigation | `hitl_used_tokens` table; `_is_token_used()` / `_mark_token_used()`; 409 on replay |

---

## Non-claims (transversal v1.7)

```
File-based signing key is not HSM-backed key custody.
Key stored unencrypted on disk — not enterprise key management.
Replay nonce store is SQLite-backed — not tamper-proof.
HITL enforcement uses HMAC shared secret — not enterprise IAM.
SQLiteAdapter is demo storage — not production audit storage.
External independent reproductions remain at 0 received.
This release is not regulatory approval.
This release is not external certification.
```
