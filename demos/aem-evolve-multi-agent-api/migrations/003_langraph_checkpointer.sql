-- AEM-EVOLVE™ v1.3 — LangGraph PostgreSQL checkpointer migration
-- Run AFTER 001_initial_schema.sql
-- Required when replacing LangGraph SqliteSaver with PostgreSQL checkpointer.
--
-- Non-claims:
--   This schema is not production-tested.
--   LangGraph checkpointer schema may evolve — verify against installed version.

CREATE TABLE IF NOT EXISTS checkpoints (
    thread_id   TEXT        NOT NULL,
    checkpoint  JSONB       NOT NULL,
    metadata    JSONB       NOT NULL DEFAULT '{}',
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (thread_id)
);

CREATE TABLE IF NOT EXISTS checkpoint_writes (
    thread_id   TEXT        NOT NULL,
    task_id     TEXT        NOT NULL,
    idx         INTEGER     NOT NULL,
    channel     TEXT        NOT NULL,
    value       BYTEA,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (thread_id, task_id, idx)
);

CREATE INDEX IF NOT EXISTS idx_checkpoint_writes_thread
    ON checkpoint_writes (thread_id);
