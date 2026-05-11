CREATE INDEX IF NOT EXISTS idx_evolution_events_thread_id
    ON evolution_events (thread_id);

CREATE INDEX IF NOT EXISTS idx_evolution_events_timestamp_utc
    ON evolution_events (timestamp_utc DESC);

CREATE INDEX IF NOT EXISTS idx_evolution_events_materiality_score
    ON evolution_events (materiality_score);

CREATE INDEX IF NOT EXISTS idx_evolution_events_requested_claim_scope
    ON evolution_events (requested_claim_scope);

CREATE INDEX IF NOT EXISTS idx_evolution_receipts_event_id
    ON evolution_receipts (event_id);

CREATE INDEX IF NOT EXISTS idx_evolution_receipts_thread_id
    ON evolution_receipts (thread_id);

CREATE INDEX IF NOT EXISTS idx_evolution_receipts_outcome
    ON evolution_receipts (outcome);

CREATE INDEX IF NOT EXISTS idx_evolution_receipts_timestamp_utc
    ON evolution_receipts (timestamp_utc DESC);
