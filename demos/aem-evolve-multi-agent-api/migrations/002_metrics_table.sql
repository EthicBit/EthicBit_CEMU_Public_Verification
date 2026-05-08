-- AEM-EVOLVE Multi-Agent Governance API
-- Migration 002: Optional persistent metrics table
-- For production deployments that want durable metric storage.
-- Compatible with: PostgreSQL 14+

CREATE TABLE IF NOT EXISTS operation_metrics (
    id            SERIAL PRIMARY KEY,
    operation     TEXT NOT NULL,
    duration_ms   DOUBLE PRECISION NOT NULL,
    thread_id     TEXT,
    recorded_at   TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_operation_metrics_operation ON operation_metrics(operation);
CREATE INDEX IF NOT EXISTS idx_operation_metrics_recorded_at ON operation_metrics(recorded_at);
