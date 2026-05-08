# AEM-EVOLVE Multi-Agent Governance API — API Reference

**Version:** 0.3.1-demo  
**Base URL:** `http://127.0.0.1:8000` (local demo)

---

## Authentication

All endpoints (except `/health` and `/healthz`) require an `X-API-Key` header.

| Role | Key (demo) | Permitted operations |
|---|---|---|
| `INITIATOR` | `demo-initiator-key-001` | `POST /start`, all read endpoints |
| `APPROVER` | `demo-approver-key-001` | `POST /approve`, all read endpoints |
| `OBSERVER` | `demo-observer-key-001` | All read endpoints |

Error responses: `401 Unauthorized` (missing/invalid key), `403 Forbidden` (wrong role).

---

## Endpoints

### GET /health

Returns the API's operational health and non-claims declaration.

**Auth:** None required.

**Response 200:**
```json
{
  "status": "healthy",
  "version": "0.3.1-demo",
  "demo_type": "technical_demonstration",
  "local_only": true,
  "tamper_evident_chain": true,
  "tamper_proof_claimed": false,
  "non_claims": ["not_production_ready", "..."]
}
```

---

### GET /healthz

Database liveness probe. Used by the benchmark and CI.

**Auth:** None required.

**Response 200:**
```json
{"status": "ok", "db": "sqlite", "version": "0.3.1-demo"}
```
`status` is `"degraded"` if the SQLite connection is unresponsive.

---

### POST /start

Initiates a new governance session. Runs the full LangGraph workflow (research → writer → governance gate). With the demo configuration (fixed `materiality_score=78.0`), the session always reaches `awaiting_human_approval`.

**Auth:** `INITIATOR` role.

**Request body:**
```json
{
  "thread_id": "my-session-001",
  "initial_prompt": "optional initial prompt (≤4096 chars)"
}
```

| Field | Type | Constraints |
|---|---|---|
| `thread_id` | string | 1–128 chars, alphanumeric/dash/underscore |
| `initial_prompt` | string | optional, ≤4096 chars |

**Response 200:**
```json
{"thread_id": "my-session-001", "status": "awaiting_human_approval"}
```

**Errors:** `401`, `403`, `422` (validation).

---

### POST /approve

Records a human approval or rejection decision for a session pending HITL review.

**Auth:** `APPROVER` role.

**Request body:**
```json
{
  "thread_id": "my-session-001",
  "decision": "approve",
  "override_reason": "Reviewed and accepted scope limitations."
}
```

| Field | Type | Values |
|---|---|---|
| `thread_id` | string | existing session |
| `decision` | string | `"approve"` \| `"reject"` |
| `override_reason` | string | optional |

**Response 200:**
```json
{"status": "completed"}
```

**Errors:** `400` (no approval pending), `401`, `403`, `404`.

---

### GET /status/{thread_id}

Returns the current state of a governance session.

**Auth:** Any valid key.

**Response 200:**
```json
{
  "thread_id": "my-session-001",
  "status": "awaiting_human_approval",
  "current_prompt": "Eres un asistente general.",
  "last_receipt": { "..." : "..." },
  "human_approval_needed": true,
  "approved_changes_count": 0
}
```

---

### GET /receipt/{thread_id}

Returns the last Evolution Receipt for a session.

**Auth:** Any valid key.

**Response 200** (Evolution Receipt):
```json
{
  "schema_id": "AEM_EVOLVE_EVOLUTION_RECEIPT_SCHEMA_V1",
  "receipt_id": "REC-EVO-API-...",
  "receipt_payload": {
    "outcome": "SCOPE_LIMITED",
    "receipt_message": "Cambio aprobado con limitaciones de scope.",
    "materiality_score": 78.0,
    "claim_boundary": { "..." : "..." },
    "requested_claim_scope": "RESEARCH_SUPPORT"
  },
  "event_id": "EVO-API-...",
  "thread_id": "my-session-001",
  "event_canonical_sha256": "...",
  "signature_status": "NOT_SIGNED_DEMO",
  "timestamp_utc": "...",
  "receipt_canonical_sha256": "..."
}
```

---

### GET /event/{thread_id}

Returns all Evolution Events for a session (most recent first).

**Auth:** Any valid key.

**Response 200:**
```json
{"thread_id": "my-session-001", "events": [ { "..." } ]}
```

---

### GET /audit/{thread_id}

Returns the full audit record for a session: events, receipts, and human decisions.

**Auth:** Any valid key.

**Response 200:**
```json
{
  "thread_id": "my-session-001",
  "events": [...],
  "receipts": [...],
  "human_decisions": [
    {
      "event_id": "EVO-API-...",
      "decision": "approve",
      "approver_id": "demo-approver-key-001",
      "override_reason": "...",
      "timestamp_utc": "..."
    }
  ]
}
```

---

### GET /chain/{thread_id}

Returns audit chain entries that reference the given thread's events, receipts, and decisions.

**Auth:** Any valid key.

**Response 200:**
```json
{
  "thread_id": "my-session-001",
  "chain_entries": [
    {
      "seq": 1,
      "entry_type": "evolution_event",
      "entry_id": "EVO-API-...",
      "entry_sha256": "...",
      "prev_chain_hash": "0000...0000",
      "chain_hash": "...",
      "timestamp_utc": "..."
    }
  ],
  "count": 2
}
```

---

### GET /chain/verify

Walks the full audit chain (all threads) and verifies every hash link. Detects insertion, deletion, or modification of any entry.

**Auth:** Any valid key.

**Response 200:**
```json
{
  "status": "PASS",
  "entries_checked": 42,
  "errors": [],
  "head_chain_hash": "...",
  "tamper_evident": true,
  "tamper_proof_claimed": false,
  "note": "Hash-linked detection only. SQLite is demo storage — not tamper-proof."
}
```

`status` values: `PASS`, `EMPTY`, `TAMPER_DETECTED`.

---

### GET /metrics

Returns live in-memory performance metrics. Resets on server restart.

**Auth:** Any valid key.

**Response 200** (see `docs/METRICS_SCHEMA.json` for full schema):
```json
{
  "counters": {
    "sessions_started": 40,
    "events_created": 40,
    "receipts_issued": 40,
    "outcome_scope_limited": 40,
    "outcome_pass": 0,
    "outcome_fail_closed": 0
  },
  "timings": {
    "end_to_end": {
      "count": 40,
      "mean_ms": 6.986,
      "median_ms": 4.077,
      "min_ms": 3.185,
      "max_ms": 53.499,
      "p95_ms": 31.49
    }
  },
  "outcome_distribution": {
    "SCOPE_LIMITED": 40,
    "PASS": 0,
    "FAIL_CLOSED": 0,
    "scope_limited_ratio": 1.0
  }
}
```

---

## Outcome Logic

| `materiality_score` | Outcome |
|---|---|
| ≤ 70 | `PASS` — auto-approved |
| 70 < score ≤ 85 | `SCOPE_LIMITED` — human approval required |
| > 85 | `FAIL_CLOSED` — blocked |

The demo configuration uses `materiality_score=78.0` (hardcoded in `writer_agent`), so all demo sessions produce `SCOPE_LIMITED`.

---

## Non-Claims

- This API is a technical demonstration, not a production system.
- `signature_status: NOT_SIGNED_DEMO` — receipts are canonically hashed but not cryptographically signed at the receipt level.
- SQLite is not production audit storage.
- `tamper_proof_claimed: false` — hash-linked chain detects tampering but does not prevent it.
- In-memory metrics are not persistent across server restarts.
