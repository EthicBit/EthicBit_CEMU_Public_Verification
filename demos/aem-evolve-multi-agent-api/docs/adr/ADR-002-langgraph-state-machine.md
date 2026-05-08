# ADR-002: LangGraph State Machine for Governance Workflow

**Status:** Accepted  
**Date:** May 2026  
**Context:** AEM-EVOLVE Multi-Agent Governance API v0.3.1-demo

## Decision

Use LangGraph `StateGraph` with `SqliteSaver` checkpointing as the multi-agent workflow engine for the governance pipeline (research → writer → governance gate → HITL / final report).

## Rationale

- **Resumable workflow state**: LangGraph checkpointing persists the workflow state to SQLite per `thread_id`. This allows `POST /approve` to resume a paused workflow without holding state in memory between requests — a critical property for HITL governance where human review may take minutes or hours.
- **Conditional routing**: `add_conditional_edges` cleanly expresses the three-way governance gate logic (PASS → auto-approve, SCOPE_LIMITED → HITL, FAIL_CLOSED → block) without custom state management.
- **Explicit node boundaries**: Each node in the graph (`research`, `writer`, `governance`, `awaiting_approval`, `final_report`) is a pure function over a state dict, making it easy to test governance logic independently.
- **Built-in thread isolation**: LangGraph scopes all state by `thread_id` via the `configurable` key, preventing session bleed-out of the box.

## Trade-offs

- LangGraph adds a non-trivial dependency (`langgraph`, `langgraph-checkpoint-sqlite`). Simpler use cases could use a plain state dict plus an explicit SQLite row.
- `StateGraph(dict)` — using a plain `dict` as the state type forgoes Pydantic validation at the graph level. Schema errors surface at runtime rather than at graph-build time.
- The `SqliteSaver` is not thread-safe for concurrent writes to the same `thread_id`. In the demo, each `thread_id` is independently scoped, so this is not a practical issue.

## Migration Path

For production, the LangGraph checkpointer must be replaced with `AsyncPostgresSaver` (or a compatible PostgreSQL-backed implementation). This is independent of the `DBAdapter` migration; both must be migrated separately.
