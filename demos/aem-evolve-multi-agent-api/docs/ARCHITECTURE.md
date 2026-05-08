# AEM-EVOLVE Multi-Agent Governance API — Architecture

**Version:** 0.3.1-demo  
**Date:** May 2026

---

## Overview

AEM-EVOLVE is a FastAPI + LangGraph application that demonstrates verifiable governance over multi-agent workflow changes. Every proposed change passes through an Evolution Gate that classifies, persists, and receipts the outcome before any downstream action is taken.

```
HTTP Client
    │
    ▼
FastAPI (main.py)
    ├── RBAC auth layer (_require_role / _require_any_auth)
    ├── Request logging middleware (duration_ms per request)
    └── Endpoints
          │
          ├── POST /start → LangGraph graph.invoke()
          │       │
          │       ├── research_agent  (stub; produces research_findings)
          │       ├── writer_agent    (proposes prompt change; creates EvolutionEvent)
          │       ├── governance_gate (evaluates receipt outcome; routes graph)
          │       └── awaiting_approval_node / final_report_node
          │
          ├── POST /approve → writes human_decision, advances graph state
          └── GET /audit, /receipt, /event, /chain, /chain/verify, /metrics, /healthz
```

---

## Key Components

### FastAPI Application (`main.py`)

Single-file server. Handles auth, routing, and wires LangGraph into HTTP endpoints. Structured JSON logging via `_JsonFormatter` emits one line per request with `duration_ms`.

### LangGraph Workflow

State machine over a Python `dict`. Nodes: `research` → `writer` → `governance` → `awaiting_approval` | `final_report`.

The governance gate reads `materiality_score` from the Evolution Event to decide the outcome:
- `≤70` → PASS (auto-approve)
- `70–85` → SCOPE_LIMITED (route to `awaiting_approval`, pause for HITL)
- `>85` → FAIL_CLOSED (block, route to `final_report`)

Checkpointing: LangGraph `SqliteSaver` persists graph state per `thread_id`, enabling the workflow to be resumed by `POST /approve`.

### Evolution Events & Receipts

**Evolution Event** — records the proposed change before evaluation:
- `event_id`, `thread_id`, `change_type`, `base_artifact`, `proposed_state`
- `materiality_score` — risk level (0–100)
- `claim_boundary` — explicit scope constraints
- `event_canonical_sha256` — SHA-256 of canonical JSON (sort_keys, no whitespace)

**Evolution Receipt** — records the gate decision:
- `receipt_payload.outcome` — PASS | SCOPE_LIMITED | FAIL_CLOSED
- `receipt_canonical_sha256` — SHA-256 of canonical receipt JSON
- `signature_status: NOT_SIGNED_DEMO` — receipts are hashed but not individually signed

Both are written to SQLite audit tables and appended to the hash-linked audit chain.

### Hash-Linked Audit Chain (`audit_chain` table)

Every governance action (event, receipt, human decision) is appended to a hash-linked chain:

```
chain_hash[n] = SHA256( chain_hash[n-1] + ":" + entry_sha256[n] )
chain_hash[0] = SHA256( GENESIS_HASH + ":" + entry_sha256[0] )
GENESIS_HASH  = "0" * 64
```

`GET /chain/verify` walks the chain and detects any insertion, deletion, or modification. This is tamper-evident, not tamper-proof — SQLite itself can be modified by a privileged actor.

### Database Adapter (`db_adapter.py`)

Abstract base `DBAdapter` with `SQLiteAdapter` (active) and `PostgresAdapter` (documented migration target). The LangGraph checkpointer uses a separate SQLite connection via `SqliteSaver`; the audit tables use the `DBAdapter`-managed connection.

### Metrics (`metrics.py`)

In-memory `MetricsRegistry` singleton. Per-operation `timer()` context manager + `increment()` counters. `snapshot()` computes count/mean/median/min/max/p95 per operation. Resets on server restart. Not thread-safe across multiple workers.

---

## Data Flow: POST /start

```
1. Validate X-API-Key → INITIATOR role
2. Build initial LangGraph state
3. graph.invoke(state, config={thread_id: ...})
   a. research_agent: sets research_findings
   b. writer_agent:
      - calls create_evolution_event() → INSERT evolution_events + audit_chain
      - calls evaluate_evolution_gate() → INSERT evolution_receipts + audit_chain
   c. governance_gate: reads outcome from receipt
      - SCOPE_LIMITED → route to awaiting_approval_node → END (paused)
      - FAIL_CLOSED   → route to final_report_node → END (blocked)
      - PASS          → route to final_report_node → END (auto-approved)
4. Return {thread_id, status}
```

## Data Flow: POST /approve

```
1. Validate X-API-Key → APPROVER role
2. graph.get_state(config) — read paused state
3. Check human_approval_needed == True
4. Apply decision: update state (approve/reject)
5. INSERT human_decisions + audit_chain
6. Call final_report_node on state
7. graph.update_state(config, state) — advance graph
8. Return {status}
```

---

## SQLite Schema

Four audit tables (see `migrations/001_initial_schema.sql`):

| Table | Purpose |
|---|---|
| `evolution_events` | Proposed change records |
| `evolution_receipts` | Gate decisions and outcomes |
| `human_decisions` | HITL approve/reject records |
| `audit_chain` | Hash-linked immutability chain |

LangGraph uses additional SQLite tables (managed by `SqliteSaver`) for workflow checkpoint state.

---

## Security Design

- **RBAC** — three roles enforced at every endpoint; fail-closed (401/403) on any violation
- **No role escalation** — approver_id is derived from the authenticated key, not the request body
- **Input validation** — `thread_id` pattern (alphanumeric/dash/underscore, ≤128), `initial_prompt` length (≤4096)
- **Tamper-evident chain** — SHA-256 hash chain over all governance actions

Full adversarial test coverage documented in `docs/ADVERSARIAL_RESILIENCE_REPORT.md`.

---

## Architecture Decision Records

See `docs/adr/` for documented design decisions:

- [ADR-001: SQLite for demo storage](adr/ADR-001-sqlite-demo-storage.md)
- [ADR-002: LangGraph state machine](adr/ADR-002-langgraph-state-machine.md)
- [ADR-003: RBAC API key scheme](adr/ADR-003-rbac-api-keys.md)

---

## Non-Claims

- Single-process; not horizontally scalable in this configuration.
- `PostgresAdapter` is a documented migration path, not an active implementation.
- In-memory metrics are not distributed or persistent.
- LangGraph `SqliteSaver` checkpointer must be separately migrated for PostgreSQL (e.g., `AsyncPostgresSaver`).
