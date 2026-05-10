# EthicBit Public Status Bulletin

Date: 2026-05-10
Scope: AEM-EVOLVE™ v1.7.0 release — read-time verification, key persistence, anti-replay

## Executive status

- Canonical branch: `main`
- Release tag: `v1.7.0`
- Official operational status: `READY`
- Full-stack verification: `FULL_STACK_VERIFICATION=PASS (21/21)`
- LLM in governance path: `false`

## Release reference

- Release tag: `v1.7.0`
- GitHub release: `https://github.com/EthicBit/EthicBit_CEMU/releases/tag/v1.7.0`

## v1.7.0 verification results

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

## What v1.7.0 adds

| Gap | Closure |
|---|---|
| Read-time signature verification | `_verify_artifact_signature()` on GET /receipt, /event, /audit; returns `signature_verified` field |
| Key persistence | `signing_key.pem` + `FileSigningProvider`; `SIGNED_Ed25519_FILE` status survives restarts |
| Replay attack mitigation | `hitl_used_tokens` table; 409 on second approve with same token |

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
