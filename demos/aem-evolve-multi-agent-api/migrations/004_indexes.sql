-- AEM-EVOLVE™ v1.4 — Performance indexes for production PostgreSQL
-- Apply after 001_initial_schema.sql, 002_metrics_table.sql, 003_langraph_checkpointer.sql
-- Safe to run multiple times.
--
-- This migration is intentionally aligned with the live schema observed in
-- staging_controlled_cloud. It does not index non-existent columns.

-- evolution_events: lookup by thread, timestamp, materiality, and requested claim scope
CREATE INDEX IF NOT EXISTS idx_evolution_events_thread_id
    ON evolution_events (thread_id);

CREATE INDEX IF NOT EXISTS idx_evolution_events_timestamp_utc
    ON evolution_events (timestamp_utc DESC);

CREATE INDEX IF NOT EXISTS idx_evolution_events_materiality_score
    ON evolution_events (materiality_score);

CREATE INDEX IF NOT EXISTS idx_evolution_events_requested_claim_scope
    ON evolution_events (requested_claim_scope);

-- evolution_receipts: lookup by event, thread, outcome, and timestamp
CREATE INDEX IF NOT EXISTS idx_evolution_receipts_event_id
    ON evolution_receipts (event_id);

CREATE INDEX IF NOT EXISTS idx_evolution_receipts_thread_id
    ON evolution_receipts (thread_id);

CREATE INDEX IF NOT EXISTS idx_evolution_receipts_outcome
    ON evolution_receipts (outcome);

CREATE INDEX IF NOT EXISTS idx_evolution_receipts_timestamp_utc
    ON evolution_receipts (timestamp_utc DESC);

-- audit_chain continuity is verified by the migration-recovery verifier.
-- No audit_chain index is declared here because the live table does not expose
-- created_at/thread_id columns in the current schema.
