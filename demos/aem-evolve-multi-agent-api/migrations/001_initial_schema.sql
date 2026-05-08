-- AEM-EVOLVE Multi-Agent Governance API
-- Migration 001: Initial audit schema
-- Compatible with: PostgreSQL 14+, SQLite 3.35+

CREATE TABLE IF NOT EXISTS evolution_events (
    event_id                TEXT PRIMARY KEY,
    thread_id               TEXT NOT NULL,
    event_canonical_sha256  TEXT NOT NULL,
    change_type             TEXT NOT NULL,
    base_artifact           TEXT NOT NULL,
    proposed_state          TEXT NOT NULL,
    materiality_score       DOUBLE PRECISION NOT NULL,
    requested_claim_scope   TEXT NOT NULL,
    timestamp_utc           TEXT NOT NULL,
    claim_boundary          TEXT NOT NULL,
    event_json              TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS evolution_receipts (
    receipt_canonical_sha256 TEXT PRIMARY KEY,
    thread_id                TEXT NOT NULL,
    event_id                 TEXT NOT NULL REFERENCES evolution_events(event_id),
    outcome                  TEXT NOT NULL,
    receipt_message          TEXT NOT NULL,
    materiality_score        DOUBLE PRECISION NOT NULL,
    claim_boundary           TEXT NOT NULL,
    requested_claim_scope    TEXT NOT NULL,
    signature_status         TEXT NOT NULL,
    timestamp_utc            TEXT NOT NULL,
    receipt_json             TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS human_decisions (
    id              SERIAL PRIMARY KEY,
    thread_id       TEXT NOT NULL,
    event_id        TEXT NOT NULL,
    decision        TEXT NOT NULL CHECK (decision IN ('approve', 'reject')),
    approver_id     TEXT NOT NULL,
    override_reason TEXT,
    timestamp_utc   TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS audit_chain (
    seq             SERIAL PRIMARY KEY,
    entry_type      TEXT NOT NULL,
    entry_id        TEXT NOT NULL,
    entry_sha256    TEXT NOT NULL,
    prev_chain_hash TEXT NOT NULL,
    chain_hash      TEXT NOT NULL,
    timestamp_utc   TEXT NOT NULL
);

-- Indexes for common query patterns
CREATE INDEX IF NOT EXISTS idx_evolution_events_thread_id     ON evolution_events(thread_id);
CREATE INDEX IF NOT EXISTS idx_evolution_receipts_thread_id   ON evolution_receipts(thread_id);
CREATE INDEX IF NOT EXISTS idx_human_decisions_thread_id      ON human_decisions(thread_id);
CREATE INDEX IF NOT EXISTS idx_audit_chain_entry_id           ON audit_chain(entry_id);
