# Release Notes — AEM-EVOLVE™ v2.0 PR 3

**Date:** 2026-05-10  
**Tag:** `v2.0-pr3`  
**Type:** v2.0 gate — PostgreSQL production persistence validation  
**Version:** `0.10.0-demo`

---

## Summary

PR 3 installs the production PostgreSQL persistence validation layer required by the v2.0
Production Readiness Gate. When `AEM_DB_URL` is configured, `PostgresProductionGate`
runs all eight mandatory evidence checks: connection, SQLite disabled, migrations, schema,
connection pooling, concurrent writes, audit-chain integrity, and backup tooling.
When `AEM_DB_URL` is not set, the gate honestly reports
`POSTGRES_PRODUCTION_PERSISTENCE_CHECK=FAIL`.

**Gate result (local/demo environment):** `POSTGRES_PRODUCTION_PERSISTENCE_CHECK=FAIL`  
*Expected — gate requires a real PostgreSQL instance.*

**Test suite:** `183 passed, 16 skipped`

---

## Changes

### `db/__init__.py` (new)
Package marker.

### `db/postgres_production_gate.py` (new)
`PostgresProductionGate` — validates all eight mandatory PR 3 evidence items:
- `from_env()` — returns None when `AEM_DB_URL` not set
- `check_connection()` — ping + PostgreSQL version
- `check_sqlite_disabled()` — `AEM_DB_ADAPTER != sqlite`
- `run_migrations()` — applies all `migrations/*.sql` files in order
- `check_schema()` — verifies all 5 tables + all required columns via `pg_tables` / `information_schema`
- `check_connection_pool()` — detects `ThreadedConnectionPool` or pgbouncer DSN
- `check_concurrent_writes(n_threads=8)` — 8-thread concurrent `INSERT` to `audit_chain`
- `check_audit_chain_integrity()` — verifies `chain_hash = SHA256(prev:sha256)` for all rows
- `check_backup_tooling()` — verifies `pg_dump` in PATH
- `gate_check()` — runs all 8 checks, returns structured result dict

Also defines `_REQUIRED_SCHEMA` — canonical table/column specification.

### `main.py` (modified)
- `_postgres_persistence_gate` module-level ref (v2.0 PR 3)
- Initialized after `build_graph()` from `PostgresProductionGate.from_env()`
- `/health` adds `postgres_persistence_gate`
- Version bumped to `0.10.0-demo`

### `tools/production_readiness/verify_postgres_persistence.py` (new)
10-check gate verifier:
- C-01: AEM_DB_URL configured (FAIL in demo — correct)
- C-02: PostgresAdapter importable
- C-03: PostgreSQL connection reachable
- C-04: SQLite not active in production mode
- C-05: Migrations applied successfully
- C-06: Schema validation PASS
- C-07: Connection pooling configured
- C-08: Concurrent writes (8-thread load test)
- C-09: Audit-chain integrity after concurrent writes
- C-10: Backup tooling available (pg_dump)

### `tests/test_postgres_persistence_gate.py` (new)
- `TestPostgresProductionGateInit` — 3 tests: from_env, URL storage
- `TestRequiredSchema` — 3 tests: schema completeness
- `TestMigrationsDirectory` — 3 tests: directory and file presence
- `TestSqliteDisabledCheck` — 3 tests: adapter detection logic
- `TestBackupTooling` — 2 tests: result structure
- `TestAuditChainIntegrityLogic` — 1 test: hash formula correctness
- `TestHealthPostgresGate` — 4 tests: health fields
- `TestLivePostgresGate` — 6 tests (skipped without `AEM_DB_URL`)
- **19 passed, 6 skipped** in isolation

### Assurance artifact
- `assurance/evolve-multi-agent/v2_0/postgres_persistence_check_report.json`

---

## Gate result (assurance artifact)

```json
{
  "gate": "POSTGRES_PRODUCTION_PERSISTENCE_CHECK",
  "result": "FAIL",
  "fail_reason": "AEM_DB_URL not configured — PostgreSQL instance required"
}
```

`FAIL` is the honest and correct result for a local/demo environment.

---

## To satisfy this gate

```bash
export AEM_DB_URL=postgresql://user:pass@host:5432/dbname
export AEM_DB_ADAPTER=postgres
python3 tools/production_readiness/verify_postgres_persistence.py
```

Required: PostgreSQL 14+, psycopg2-binary, pg_dump in PATH.

---

## Non-claims

```
POSTGRES_PRODUCTION_PERSISTENCE_CHECK=FAIL — gate not satisfied in local/demo environment.
This PR does not certify enterprise-scale database performance.
pgbouncer configuration requires separate infrastructure evidence.
Backup/restore schedule requires separate operational evidence.
This PR does not grant regulatory approval.
PASS requires a real PostgreSQL instance — not SQLite.
This release is not regulatory approval.
This release is not external certification.
```
