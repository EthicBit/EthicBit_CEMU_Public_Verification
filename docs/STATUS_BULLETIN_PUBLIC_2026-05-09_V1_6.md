# EthicBit Public Status Bulletin

Date: 2026-05-09
Scope: AEM-EVOLVE™ v1.6.0 release — critical gaps closure

## Executive status

- Canonical branch: `main`
- Release tag: `v1.6.0`
- Official operational status: `READY`
- Full-stack verification: `FULL_STACK_VERIFICATION=PASS (18/18)`
- LLM in governance path: `false`

## Release reference

- Release tag: `v1.6.0`
- PRs merged: #133 · #134 · #138
- GitHub release: `https://github.com/EthicBit/EthicBit_CEMU/releases/tag/v1.6.0`

## v1.6.0 verification results

```
FULL_STACK_VERIFICATION=PASS  (18/18)
  v1.1: 6/6  ·  v1.2: 2/2  ·  v1.3: 4/4  ·  v1.4: 2/2  ·  v1.5: 2/2  ·  v1.6: 2/2

  V1_6-SIGNED-RECEIPTS    SIGNED_RECEIPTS_VERIFICATION=PASS (10/10)
  V1_6-E2E-API            E2E_API_VERIFICATION=PASS (10/10)
```

```bash
python3 demos/aem-evolve-multi-agent-api/tools/reproduction/verify_all_v1_6.py
```

## What v1.6.0 adds

| PR | Gap closed |
|---|---|
| #133 | SigningProvider wired — Ed25519 signatures on all events/receipts; HITL token enforced in /approve; SQLiteAdapter activated |
| #134 | E2E integration test (10/10) + verify_all_v1_6.py (18/18) + CI workflow updated |
| #138 | Whitepaper v1.6 |

## Non-claims (transversal v1.6)

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
