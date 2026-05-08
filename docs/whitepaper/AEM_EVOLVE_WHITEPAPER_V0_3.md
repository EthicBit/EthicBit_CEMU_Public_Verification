# AEM-EVOLVE™ — Whitepaper v0.3

**Verifiable Multi-Agent Governance for Controlled Environments**

**Version:** 0.3 (Phase 1 — Foundation & Independent Verification)  
**Base system version:** v0.3.1-demo  
**Date:** May 2026  
**Status:** Technical whitepaper — controlled demonstration stage

---

## Abstract

AEM-EVOLVE™ (Adaptive Evidence-based Multi-agent Evolution) is a governance framework for multi-agent AI workflows that requires each proposed workflow change to be evaluated, receipted, and approved through a human-in-the-loop gate before it takes effect. This whitepaper describes the v0.3.1-demo system, its verifiable properties, its explicit limitations, and the roadmap from controlled demonstration to v1.0.

---

## 1. Problem Statement

Multi-agent AI systems can propose changes to their own configuration, prompts, or behavior autonomously. Without a structured governance layer, such changes are invisible, unaudited, and irreversible. In regulated or sensitive environments — financial services, healthcare, critical infrastructure — this creates accountability gaps that are incompatible with responsible AI deployment.

AEM-EVOLVE™ addresses this by interposing a governance layer between any proposed workflow change and its execution.

---

## 2. System Design

### 2.1 Core Components

| Component | Role |
|---|---|
| FastAPI + Uvicorn | HTTP API layer |
| LangGraph `StateGraph` | Multi-agent workflow graph |
| SQLite (demo) | Audit persistence (4 tables) |
| Evolution Event | Canonical-hashed record of a proposed change |
| Evolution Receipt | Scoped governance decision on the event |
| HITL Gate | Human-in-the-loop approval endpoint |
| Audit Chain | SHA-256 hash-linked append-only audit log |

### 2.2 Governance Flow

```
Agent proposes change
        ↓
POST /start → research_agent → writer_agent
        ↓
create_evolution_event()
  event_canonical_sha256 = SHA256(canonical_json(event))
        ↓
evaluate_evolution_gate()
  outcome ∈ {PASS, SCOPE_LIMITED, FAIL_CLOSED}
        ↓
  PASS        → auto-approved, appended to audit chain
  SCOPE_LIMITED → awaiting_approval_node → POST /approve required
  FAIL_CLOSED → rejected, no further action
        ↓
_append_audit_chain()
  chain_hash = SHA256(prev_chain_hash + ":" + entry_sha256)
```

### 2.3 Role-Based Access Control

| Role | Permitted endpoints |
|---|---|
| INITIATOR | `POST /start`, `GET /status`, `GET /audit` |
| APPROVER | `POST /approve`, `GET /status`, `GET /audit` |
| OBSERVER | `GET /status`, `GET /audit`, `GET /chain` |

All endpoints are fail-closed: missing or invalid key → 401; wrong role → 403.

### 2.4 Cryptographic Properties

| Property | Implementation |
|---|---|
| Canonical hashing | `json.dumps(sort_keys=True, separators=(',',':'), ensure_ascii=False)` → SHA-256 |
| Audit chain | `chain_hash = SHA256(prev_chain_hash + ":" + entry_sha256)` |
| Manifest signatures | Ed25519 (demo key, locally verifiable) |
| On-chain anchor | Ethereum mainnet self-send transaction carrying manifest hash as calldata |

---

## 3. Verifiable Claims (v0.3.1-demo)

The following claims are verifiable by any party from the public repository at commit `c634f906`:

1. **Canonical-hashed Evolution Events and Receipts** — every governance event carries a deterministic SHA-256 over its canonical JSON representation.

2. **Scope-limited Evolution Receipts** — receipts carry explicit `claim_boundary` fields; they do not claim production validity, clinical use, or regulatory approval.

3. **Hash-linked audit chain** — every audit chain entry commits to the previous entry's `chain_hash`; any tampering is detectable by re-running `verify_aem_evolve_multi_agent_audit_chain.py`.

4. **Fail-closed RBAC HITL gate** — the `/approve` endpoint rejects all requests lacking a valid APPROVER key; all other roles receive 403.

5. **Ed25519-signed demo receipts** — the anchor receipt and manifest are signed with a published demo public key; signatures are verifiable with `openssl pkeyutl -verify`.

6. **Ethereum mainnet anchor** — the demo manifest was anchored at TX `0x30fc9e6c810078c42ac1b840c3712d165342436ec427471b7f955425ea4b8275`, block 25 045 091.

7. **Structured JSON logging** — all API requests and audit chain events are logged as structured JSON to stdout.

8. **Reproducible in under 30 minutes** — using `QUICKSTART_30_MIN.md` on any standard developer machine with Python 3.10+.

---

## 4. Explicit Non-Claims

| Non-claim | Rationale |
|---|---|
| Not production-ready | SQLite storage; demo keys; no TLS; no connection pool |
| Not independently reproduced | Phase 1 threshold (3–5 reports) not yet met |
| Not tamper-proof | Tamper-evident only; SQLite can be modified outside the API |
| Not HSM-backed | Demo key is a local PEM file |
| Not regulatory-approved | No regulatory assessment has been initiated |
| Not clinical or diagnostic | No clinical use case has been scoped |
| Not financial advice | Sectorial demo does not constitute financial guidance |
| Not cybersecurity certification | Adversarial testing (Phase 2) not yet complete |
| Not externally certified | No third-party review engagement active |

---

## 5. Evidence Package

All claims are backed by verifiable artifacts in the public repository:

| Artifact | Path |
|---|---|
| Manifest (signed) | `assurance/evolve-multi-agent/AEM_EVOLVE_MULTI_AGENT_API_MANIFEST.json` |
| Signature set | `assurance/evolve-multi-agent/AEM_EVOLVE_MULTI_AGENT_API_SIGNATURE_SET.json` |
| Anchor receipt | `assurance/evolve-multi-agent/AEM_EVOLVE_MULTI_AGENT_API_ANCHOR_RECEIPT.json` |
| Demo public key | `assurance/evolve-multi-agent/AEM_EVOLVE_MULTI_AGENT_API_DEMO_PUBLIC_KEY.pem` |
| Hash record (25 entries) | `assurance/evolve-multi-agent/AEM_EVOLVE_MULTI_AGENT_API_HASH_RECORD.txt` |
| Reproduction challenge | `assurance/evolve-multi-agent/AEM_EVOLVE_MULTI_AGENT_API_REPRODUCTION_CHALLENGE.json` |
| Execution export (11 artifacts) | `assurance/evolve-multi-agent/execution/` |
| Assurance ladder conditions | `demos/aem-evolve-multi-agent-api/docs/ASSURANCE_LADDER_CONDITIONS.md` |
| v1.0 Roadmap | `docs/roadmap/AEM_EVOLVE_V1_0_ROADMAP.md` |

---

## 6. Roadmap to v1.0

| Phase | Version | Definition |
|---|---|---|
| 0 (complete) | v0.3.1-demo | Anchored Controlled Demonstration |
| 1 (current) | v0.3.5 | Independent Verification (3–5 reproductions) |
| 2 | v0.4 | Adversarial Resilience |
| 3 | v0.5 | Metrics + PostgreSQL Architecture |
| 4 | v0.6/v0.9 | Quality + Documentation |
| 5 | v1.0.0 | Public Launch (target: 2026-Q3) |

**v1.0 definition:** Reproducible + Measured + Adversarially Tested + Usable in Controlled Environments.

Full roadmap: `docs/roadmap/AEM_EVOLVE_V1_0_ROADMAP.md`

---

## 7. How to Reproduce

See `docs/reproduction/REPRODUCTION_GUIDE.md` for the complete guide.  
See `demos/aem-evolve-multi-agent-api/QUICKSTART_30_MIN.md` for the 30-minute path.  
Submit reports to `independent-reproductions/` via pull request.

---

## 8. Changelog

| Version | Date | Changes |
|---|---|---|
| v0.1 | 2026-05 | Initial demo package (PR 1) |
| v0.2 | 2026-05 | Mainnet anchor + Ed25519 signatures + tamper-evident chain (PRs 2–4) |
| v0.3 | 2026-05 | Reproduction challenge + RBAC HITL + production hardening + execution export + roadmap (PRs 5–7, 7.1, 7.2) |

---

*AEM-EVOLVE™ is developed by EthicBit as part of the CEMU (Controlled Evidence-based Multi-agent Units) public verification series.*
