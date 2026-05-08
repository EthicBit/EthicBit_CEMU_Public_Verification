# ADR-001: SQLite for Demo Storage

**Status:** Accepted  
**Date:** May 2026  
**Context:** AEM-EVOLVE Multi-Agent Governance API v0.3.1-demo

## Decision

Use SQLite as the primary database for audit tables (`evolution_events`, `evolution_receipts`, `human_decisions`, `audit_chain`) and for the LangGraph checkpoint store (`SqliteSaver`).

## Rationale

- **Zero-infrastructure dependency**: A reproducer can clone and run `python main.py` without provisioning any external service. This directly supports the Phase 1 reproducibility goal (30-minute quickstart).
- **File-level portability**: The `.db` file can be copied, inspected with `sqlite3 CLI`, and included in execution export packages without additional tooling.
- **LangGraph compatibility**: `langgraph-checkpoint-sqlite` is the officially supported in-process checkpointer; it requires no additional setup.
- **Scope**: The demo measures governance semantics, not database throughput. SQLite is sufficient for single-process benchmarking (median e2e: 4 ms).

## Trade-offs

- Not suitable for multi-process or multi-worker deployments (SQLite WAL mode partially mitigates contention but is not designed for horizontal scale).
- No network isolation — the `.db` file is directly accessible to any process with filesystem access. This is consistent with the non-claim `tamper_proof_claimed: false`.
- LangGraph `SqliteSaver` must be separately migrated to `AsyncPostgresSaver` (or equivalent) for production.

## Migration Path

`db_adapter.py` defines `PostgresAdapter` as a drop-in replacement. SQL migration scripts in `migrations/` are PostgreSQL 14+ compatible. See `ARCHITECTURE.md` for the migration path.
