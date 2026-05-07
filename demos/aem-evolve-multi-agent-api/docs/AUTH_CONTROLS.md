# AEM-EVOLVE Multi-Agent Governance API — Auth Controls

**Version:** 0.3.1-demo  
**Assurance ladder milestone:** PR 6 — Production Authentication / Authorization

---

## Scheme

`X-API-Key` header. Keys are mapped to roles in `configs/auth_demo_keys.json`.

## Roles

| Role | Permitted endpoints |
|---|---|
| `INITIATOR` | `POST /start` |
| `APPROVER` | `POST /approve` (HITL gate) |
| `OBSERVER` | `GET /status`, `/audit`, `/receipt`, `/event`, `/chain/*` |

All roles may call `GET /health`.

## HITL Gate Enforcement

`POST /approve` requires role `APPROVER`. Requests with a missing key, invalid key, or wrong role are rejected **before** the approval logic executes:

- Missing `X-API-Key` → **401 Unauthorized**
- Invalid key → **401 Unauthorized**
- Valid key, wrong role → **403 Forbidden**
- Valid key, correct role → **proceed** (200 or 400/404 from business logic)

The authenticated key identity is recorded as `approver_id` in `human_decisions` and in the audit chain. The approver cannot self-assign an arbitrary identity.

## Demo Keys

Demo keys are in `configs/auth_demo_keys.json`:

| Key | Role |
|---|---|
| `demo-initiator-key-001` | INITIATOR |
| `demo-approver-key-001` | APPROVER |
| `demo-observer-key-001` | OBSERVER |

The template for custom keys is in `configs/auth_demo_keys.json.template`.

Keys may also be supplied via the environment variable `AEM_DEMO_AUTH_KEYS_JSON` (JSON string, same schema as the file).

## Non-Claims

This auth implementation does NOT claim:

- Production-grade identity provider (no OAuth2, no JWT, no MFA)
- HSM-backed key storage
- Key rotation enforcement
- Multi-tenant isolation
- Production secret management (keys are in a local file)
- Rate limiting (planned PR 7)
- HTTPS enforcement (planned PR 7)

## Verification

```bash
# With API running (python main.py):
bash demos/aem-evolve-multi-agent-api/scripts/verify_auth_controls.sh
```

Expected: `AEM_EVOLVE_AUTH_CONTROLS_STATUS=PASS`
