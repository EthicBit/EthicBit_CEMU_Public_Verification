-- AEM-EVOLVE™ v2.0 PR 4 — Rollback migration for 003_langraph_checkpointer.sql
-- Compatible with: PostgreSQL 14+

DROP TABLE IF EXISTS checkpoint_writes;
DROP TABLE IF EXISTS checkpoints;
