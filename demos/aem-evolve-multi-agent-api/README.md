# AEM-EVOLVE™ Multi-Agent Governance API Technical Demonstration

**Version:** 0.3.1-demo  
**Date:** May 2026  
**Status:** Technical Demonstration  
**Series:** EthicBit/CEMU Public Verification Series  

---

## 1. Overview

This demonstration implements an API-based multi-agent governance workflow using:

- FastAPI
- LangGraph
- SQLite checkpoints
- Explicit audit tables
- AEM-EVOLVE™-style Evolution Events
- AEM-EVOLVE™-style Evolution Receipts
- Human-in-the-Loop approval
- Scope-limited governance outcomes

The demo shows how proposed changes inside a multi-agent workflow can be converted into structured governance events, evaluated by a gate, persisted as receipts, and routed to human review when required.

**This is a technical demonstration only.** It is not production-ready, independently reproduced, externally certified, or intended for regulated, clinical, diagnostic, or production use.

---

## 2. Strategic Context

This demo belongs to the EthicBit Mechanical Ethics Assurance stack.

The broader EthicBit thesis is:

> AEM V1.1 verifies the artifact.  
> AEM-EVOLVE™ governs the change.  
> GitHub exposes the evidence.  
> Ethereum mainnet anchors the integrity.

This demo focuses specifically on the second layer:

**AEM-EVOLVE™ governs the change.**

It demonstrates that AEM-EVOLVE™-style governance can apply not only to release artifacts, but also to material changes inside multi-agent workflows.

---

## 3. What This Demo Demonstrates

- A multi-agent workflow with research and writer agents
- A proposed agent configuration change
- Creation of an Evolution Event
- Evaluation through an AEM-EVOLVE™-style governance gate
- Generation of an Evolution Receipt
- Explicit claim boundaries
- Canonical SHA-256 hashing for events and receipts
- SQLite checkpoint persistence
- Explicit audit tables for events, receipts, and human decisions
- Human-in-the-Loop approval for `SCOPE_LIMITED` outcomes
- Fail-closed behavior for high-risk changes
- API endpoints for status, receipts, events, audit records, and health

---

## 4. Architecture

```text
Client
  ↓
FastAPI
  ↓
LangGraph Workflow
  ↓
Research Agent
  ↓
Writer Agent proposes configuration change
  ↓
Evolution Event
  ↓
AEM-EVOLVE™ Governance Gate
  ↓
Evolution Receipt
  ↓
Outcome:
  ├── PASS → auto-approve
  ├── SCOPE_LIMITED → human approval required
  └── FAIL_CLOSED → change blocked
  ↓
SQLite Checkpoints + Explicit Audit Tables
```

---

## 5. Workflow

### Step 1 — Start Session

```http
POST /start
```

### Step 2 — Evolution Event

The proposed change is converted into a structured **Evolution Event**.

### Step 3 — Evolution Gate

The gate evaluates the change and produces one of the following outcomes:

| Materiality Score | Outcome |
|---:|---|
| ≤ 70 | `PASS` |
| 71 – 85 | `SCOPE_LIMITED` |
| > 85 | `FAIL_CLOSED` |

### Step 4 — Evolution Receipt

A formal receipt is generated and stored.

See:

```text
docs/EVOLUTION_RECEIPTS_SPECIFICATION.md
```

### Step 5 — Human-in-the-Loop

When the outcome is `SCOPE_LIMITED`, a human must approve or reject the change via:

```http
POST /approve
```

---

## 6. SQLite Persistence

This demo uses SQLite for two purposes:

- **LangGraph Checkpoints:** workflow state continuity
- **Explicit Audit Tables:** `evolution_events`, `evolution_receipts`, `human_decisions`

SQLite is used for **demonstration persistence only**. It is not presented as production-grade concurrent audit storage.

---

## 7. API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| POST | `/start` | Start a workflow session |
| GET | `/status/{thread_id}` | Get current workflow status |
| POST | `/approve` | Human approval/rejection |
| GET | `/event/{thread_id}` | Get Evolution Events |
| GET | `/receipt/{thread_id}` | Get latest receipt |
| GET | `/audit/{thread_id}` | Get full audit trail: events, receipts, decisions |
| GET | `/health` | Health check and non-claims |

---

## 8. How to Run

```bash
pip install -r requirements.txt
python main.py
```

API available at:

```text
http://127.0.0.1:8000
```

Interactive docs:

```text
http://127.0.0.1:8000/docs
```

---

## 9. Local Verification Scripts

After the local API server is running, execute:

```bash
bash scripts/run_demo_e2e.sh
bash scripts/run_tamper_checklist.sh
```

Expected controlled-demo output:

```text
AEM_EVOLVE_MULTI_AGENT_API_DEMO_STATUS=PASS
SIGNATURE_STATUS=NOT_SIGNED_DEMO
SIMULATED_TAMPER_CHECKLIST=PASS
```

These checks verify endpoint behavior and the documented demo boundary. They do not convert the package into a signed, anchored, production-ready, or independently reproduced release.

---

## 10. Example Local Test Flow

Start a session:

```bash
curl -X POST http://127.0.0.1:8000/start \
  -H "Content-Type: application/json" \
  -d '{
    "thread_id": "demo-thread-001",
    "initial_prompt": "Eres un asistente general."
  }'
```

Check status:

```bash
curl http://127.0.0.1:8000/status/demo-thread-001
```

Inspect latest receipt:

```bash
curl http://127.0.0.1:8000/receipt/demo-thread-001
```

Approve the `SCOPE_LIMITED` change:

```bash
curl -X POST http://127.0.0.1:8000/approve \
  -H "Content-Type: application/json" \
  -d '{
    "thread_id": "demo-thread-001",
    "decision": "approve",
    "approver_id": "human-reviewer",
    "override_reason": "Approved for research-support scope only."
  }'
```

Inspect full audit trail:

```bash
curl http://127.0.0.1:8000/audit/demo-thread-001
```

---

## 11. Claims

This technical demonstration supports the following claims:

- It demonstrates an API-based multi-agent AEM-EVOLVE™-style governance workflow.
- It converts proposed agent configuration changes into Evolution Events.
- It evaluates proposed changes through a scope-limited governance gate.
- It generates Evolution Receipts with canonical SHA-256 hashes.
- It persists workflow state through SQLite checkpoints.
- It stores events, receipts, and human decisions in explicit audit tables.
- It routes `SCOPE_LIMITED` changes to Human-in-the-Loop approval.
- It blocks `FAIL_CLOSED` changes from automatic approval.

---

## 12. Non-Claims

This demonstration does **not** claim:

- Production readiness
- Independent reproduction
- Cryptographically signed release receipts
- Ethereum mainnet anchoring for this demo package
- Regulatory approval
- Clinical or diagnostic suitability
- External certification
- Production authentication or authorization
- Tamper-proof audit trail
- Third-party binding
- Full AEM-EVOLVE™ production implementation
- SQLite as production-grade concurrent audit storage

---

## 13. Related Specification

See:

```text
docs/EVOLUTION_RECEIPTS_SPECIFICATION.md
```

for the formal specification of Evolution Receipts.

---

## 14. Relationship to EthicBit Unified Stack

This demo extends the EthicBit Unified Stack by showing how AEM-EVOLVE™-style governance can apply inside a multi-agent workflow.

```text
AEM V1.1 verifies the artifact.
AEM-EVOLVE™ governs the change.
Human-in-the-Loop controls scope-limited changes.
SQLite checkpoints preserve workflow continuity.
Explicit audit tables expose events, receipts, and decisions.
```

This demo does not replace the existing AEM-EVOLVE™ v0.3 technical demonstration release. It is an additional technical demonstration of AEM-EVOLVE™-style governance applied to multi-agent API workflows.

---

**Document maintained as part of the EthicBit/CEMU Public Verification Series.**

Technical demonstration only. No regulatory, clinical, diagnostic, production-readiness, independent reproduction, or third-party certification claim is made.
