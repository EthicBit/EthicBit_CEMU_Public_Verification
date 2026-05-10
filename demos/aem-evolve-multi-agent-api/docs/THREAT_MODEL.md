# AEM-EVOLVE™ Multi-Agent Governance API — Threat Model

**Version:** 0.4 (Phase 2 — Security & Adversarial Resilience)  
**Scope:** Demo deployment on localhost. Not a production threat model.

---

## Assets

| Asset | Sensitivity | Location |
|---|---|---|
| Evolution Events | Medium — governance record | SQLite `evolution_events` table |
| Evolution Receipts | Medium — governance decision | SQLite `evolution_receipts` table |
| Audit Chain | High — integrity anchor | SQLite `audit_chain` table |
| HITL Decisions | High — human approval record | SQLite `human_decisions` table |
| API Keys | High — access control | `configs/auth_demo_keys.json` |
| Ed25519 Private Key | High — signing key | `assurance/keys/` (gitignored) |
| Manifest + Receipts | Medium — assurance artifacts | `assurance/evolve-multi-agent/` |

---

## Threat Actors

| Actor | Capability | Goal |
|---|---|---|
| Malicious agent | Can call API endpoints | Inject unauthorized changes; bypass governance gate |
| Unauthorized approver | Has no APPROVER key | Approve changes without authorization |
| Data tamperer | Has filesystem access | Modify SQLite records to fabricate approvals or erase decisions |
| Prompt injector | Can craft API payloads | Inject adversarial content into thread_id or prompts |
| Key thief | Has filesystem access | Steal API keys; impersonate roles |

---

## Attack Surface

| Endpoint | Auth required | Risk |
|---|---|---|
| `POST /start` | INITIATOR | Malicious thread_id or oversized prompt |
| `POST /approve` | APPROVER only | Unauthorized approval; role escalation |
| `GET /status` | Any valid key | Information disclosure |
| `GET /audit/{thread_id}` | Any valid key | Audit log enumeration |
| `GET /chain/{thread_id}` | Any valid key | Chain inspection |
| `GET /chain/verify` | Any valid key | Integrity check (read-only) |
| SQLite file | Filesystem | Direct DB tampering |
| `configs/auth_demo_keys.json` | Filesystem | Key disclosure |

---

## Mitigations In Place

| Threat | Mitigation | Strength |
|---|---|---|
| Unauthorized approval | RBAC fail-closed: APPROVER role required; 401/403 on all other paths | Strong (demo) |
| Prompt injection in thread_id | Pydantic `field_validator`: alphanumeric/dash/underscore only, max 128 chars | Strong |
| Oversized inputs | `field_validator`: thread_id ≤128, initial_prompt ≤4096 | Strong |
| Malformed JSON | FastAPI/Pydantic: returns 422 before any processing | Strong |
| Audit chain tampering | Hash-linked chain: any mutation propagates to `TAMPER_DETECTED` on verify | Strong (tamper-evident) |
| Event/receipt SHA-256 forgery | Canonical SHA-256 over canonical JSON; verifier re-computes on read | Strong |
| Role escalation | No privilege escalation path; keys map to fixed roles; no role modification endpoint | Strong (demo) |
| HITL token replay attack | `hitl_used_tokens` table: one-time-use per (token_hash, event_id) pair; 409 on replay | Strong |
| OIDC provider outage | Dual-path fallback (HMAC demo path); `oidc_provider_outage` counter alerts ops | Medium |
| KMS signing failure | `kms_signing_failed` counter + Prometheus alert; runbook INC-06 documents recovery | Medium |

---

## Residual Risks (Demo Scope)

| Risk | Status | Mitigation path |
|---|---|---|
| SQLite file directly writable | **Open** — demo only | Production: PostgreSQL + OS-level access controls |
| API keys in plaintext JSON file | **Open** — demo only | Production: secrets manager (Vault, AWS Secrets Manager) |
| No TLS | **Open** — demo only | Production: TLS at reverse proxy |
| No rate limiting | **Open** — demo only | Production: API gateway rate limits |
| Demo Ed25519 key is local PEM | **Open** — demo only | Production: HSM-backed key |
| No session expiry | **Open** — demo only | Production: short-lived tokens |
| Structured logs contain path info | Low | Scrub sensitive fields before production |

---

## Out of Scope (Demo)

- Network-level attacks (no external exposure in demo).
- Supply chain attacks on dependencies.
- LangGraph checkpoint DB contents (not audited as governance data).
- Cryptographic key generation security.

---

## Non-Claims

This threat model covers the demo deployment only. It does not constitute a production security assessment, penetration test, or regulatory risk analysis.
