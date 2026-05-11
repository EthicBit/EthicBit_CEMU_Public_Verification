-- AEM-EVOLVE™ v1.7/v2.0 — HITL replay mitigation persistence
-- Required for one-time-use HITL token/event replay protection evidence.

CREATE TABLE IF NOT EXISTS hitl_used_tokens (
    token_hash TEXT NOT NULL,
    event_id TEXT NOT NULL,
    used_at_utc TEXT NOT NULL,
    approver_identity TEXT,
    PRIMARY KEY (token_hash, event_id)
);

CREATE INDEX IF NOT EXISTS idx_hitl_used_tokens_event_id
    ON hitl_used_tokens (event_id);

CREATE INDEX IF NOT EXISTS idx_hitl_used_tokens_used_at_utc
    ON hitl_used_tokens (used_at_utc DESC);
