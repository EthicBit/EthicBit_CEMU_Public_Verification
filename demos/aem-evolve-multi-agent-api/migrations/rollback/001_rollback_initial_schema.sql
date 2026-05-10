-- AEM-EVOLVE™ v2.0 PR 4 — Rollback migration for 001_initial_schema.sql
-- CAUTION: Drops all audit tables. Execute only after confirmed backup/restore.
-- Compatible with: PostgreSQL 14+
--
-- Rollback procedure:
--   1. pg_dump the database to a timestamped file (backup evidence)
--   2. Confirm AEM service is stopped
--   3. Execute this file: psql $AEM_DB_URL < 001_rollback_initial_schema.sql
--   4. Restore from backup if rollback fails: psql $AEM_DB_URL < backup.sql
--   5. Verify audit chain is preserved in backup
--
-- Non-claims:
--   This rollback does not preserve audit data — backup is required first.
--   Zero-data-loss rollback requires a restore from backup, not this DROP.

DROP TABLE IF EXISTS hitl_used_tokens;
DROP TABLE IF EXISTS audit_chain;
DROP TABLE IF EXISTS human_decisions;
DROP TABLE IF EXISTS evolution_receipts;
DROP TABLE IF EXISTS evolution_events;
