-- AEM-EVOLVE™ v1.4 — Performance indexes for production PostgreSQL
-- Apply after 001_initial_schema.sql, 002_metrics_table.sql, 003_langraph_checkpointer.sql
-- Safe to run multiple times (IF NOT EXISTS / CREATE INDEX CONCURRENTLY)

-- evolution_events: lookup by status and timestamp
CREATE INDEX IF NOT EXISTS idx_evolution_events_status
    ON evolution_events (status);

CREATE INDEX IF NOT EXISTS idx_evolution_events_created_at
    ON evolution_events (created_at DESC);

-- evolution_receipts: lookup by event_id and outcome
CREATE INDEX IF NOT EXISTS idx_evolution_receipts_event_id
    ON evolution_receipts (event_id);

CREATE INDEX IF NOT EXISTS idx_evolution_receipts_outcome
    ON evolution_receipts (recommended_outcome);

-- audit_chain: lookup by thread_id for chain verification
CREATE INDEX IF NOT EXISTS idx_audit_chain_thread_id
    ON audit_chain (thread_id);

CREATE INDEX IF NOT EXISTS idx_audit_chain_created_at
    ON audit_chain (created_at DESC);
