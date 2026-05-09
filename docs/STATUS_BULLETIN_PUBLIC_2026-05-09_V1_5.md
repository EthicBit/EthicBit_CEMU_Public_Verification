# EthicBit Public Status Bulletin

Date: 2026-05-09
Scope: AEM-EVOLVE™ v1.5.0 release — enterprise hardening update

## Executive status

- Canonical branch: `main`
- Release tag: `v1.5.0`
- Official operational status: `READY`
- Full-stack verification: `FULL_STACK_VERIFICATION=PASS (16/16)`
- LLM in governance path: `false`

## Release reference

- Release tag: `v1.5.0`
- Canonical merge commit on `main`: `8297a0c1`
- PRs merged: #126 · #127 · #128 · #129 · #130 · #131 · #132
- GitHub release: `https://github.com/EthicBit/EthicBit_CEMU/releases/tag/v1.5.0`

## v1.5.0 verification results

```
FULL_STACK_VERIFICATION=PASS  (16/16)
  v1.1: 6/6  ·  v1.2: 2/2  ·  v1.3: 4/4  ·  v1.4: 2/2  ·  v1.5: 2/2

  V1_5-HSM-SIGNING     HSM_SIGNING_VERIFICATION=PASS (10/10)
  V1_5-OIDC-HITL       OIDC_HITL_VERIFICATION=PASS (10/10)
```

```bash
python3 demos/aem-evolve-multi-agent-api/tools/reproduction/verify_all_v1_5.py
```

## What v1.5.0 adds

| PR | Gap closed |
|---|---|
| #127 | `Pkcs11SigningProvider` + `KmsSigningProvider` — PKCS#11 / AWS KMS stubs |
| #128 | OIDC RS256 JWT HITL verifier — inline JWKS, no IdP required for CI |
| #129 | Runtime dependency validator (REQUIRED/OPTIONAL) + server smoke test |
| #130 | N=20 async concurrency test + pgbouncer integration guide |
| #131 | v1.4 reproduction challenge + 16-check full-stack verifier |
| #132 | Whitepaper v1.5 |

## Non-claims (transversal v1.5)

```
PKCS#11 provider is not a real HSM integration.
KMS provider is not a real AWS KMS integration.
OIDC verifier uses locally generated JWKS — not a real IdP.
AsyncPostgresAdapter concurrency test uses mocks, not a live database.
External independent reproductions remain at 0 received.
This release is not regulatory approval.
This release is not external certification.
```
