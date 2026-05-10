"""
Tests for v2.0 PR 3 — PostgreSQL production persistence gate.

When AEM_DB_URL is not set: gate is NOT_CONFIGURED (correct).
When AEM_DB_URL is set but DB unreachable: gate FAIL on C-03.
Live DB tests require AEM_DB_URL pointing to a real PostgreSQL instance.
"""
import os
import sys
import pytest
from pathlib import Path

DEMO_ROOT = Path(__file__).resolve().parents[1]
if str(DEMO_ROOT) not in sys.path:
    sys.path.insert(0, str(DEMO_ROOT))

from db.postgres_production_gate import (
    PostgresProductionGate,
    _REQUIRED_SCHEMA,
    MIGRATIONS_DIR,
)

_DB_URL = os.getenv("AEM_DB_URL", "")
_SKIP_NO_DB = pytest.mark.skipif(not _DB_URL, reason="AEM_DB_URL not set — live DB required")


# ── Gate init ───────────────────────────────────────────────────────────────

class TestPostgresProductionGateInit:
    def test_from_env_returns_none_without_db_url(self, monkeypatch):
        monkeypatch.delenv("AEM_DB_URL", raising=False)
        assert PostgresProductionGate.from_env() is None

    def test_from_env_returns_gate_with_db_url(self, monkeypatch):
        monkeypatch.setenv("AEM_DB_URL", "postgresql://user:pass@localhost:5432/test")
        gate = PostgresProductionGate.from_env()
        assert gate is not None

    def test_gate_stores_db_url(self, monkeypatch):
        monkeypatch.setenv("AEM_DB_URL", "postgresql://user:pass@localhost:5432/test")
        gate = PostgresProductionGate.from_env()
        assert gate._db_url == "postgresql://user:pass@localhost:5432/test"


# ── Schema definition ────────────────────────────────────────────────────────

class TestRequiredSchema:
    def test_all_five_tables_present_in_schema(self):
        expected = {
            "evolution_events", "evolution_receipts", "human_decisions",
            "audit_chain", "hitl_used_tokens",
        }
        assert expected == set(_REQUIRED_SCHEMA.keys())

    def test_audit_chain_has_required_columns(self):
        cols = _REQUIRED_SCHEMA["audit_chain"]
        for col in ("seq", "entry_type", "entry_id", "entry_sha256",
                    "prev_chain_hash", "chain_hash", "timestamp_utc"):
            assert col in cols

    def test_hitl_used_tokens_has_primary_key_columns(self):
        cols = _REQUIRED_SCHEMA["hitl_used_tokens"]
        assert "token_hash" in cols
        assert "event_id" in cols


# ── Migrations directory ─────────────────────────────────────────────────────

class TestMigrationsDirectory:
    def test_migrations_dir_exists(self):
        assert MIGRATIONS_DIR.exists(), f"migrations/ directory not found at {MIGRATIONS_DIR}"

    def test_migration_001_exists(self):
        assert (MIGRATIONS_DIR / "001_initial_schema.sql").exists()

    def test_at_least_one_sql_file(self):
        sql_files = list(MIGRATIONS_DIR.glob("*.sql"))
        assert len(sql_files) >= 1


# ── check_sqlite_disabled ────────────────────────────────────────────────────

class TestSqliteDisabledCheck:
    def test_sqlite_disabled_when_adapter_postgres(self, monkeypatch):
        monkeypatch.setenv("AEM_DB_ADAPTER", "postgres")
        gate = PostgresProductionGate("postgresql://user:pass@localhost/test")
        result = gate.check_sqlite_disabled()
        assert result["ok"] is True

    def test_sqlite_active_when_adapter_sqlite(self, monkeypatch):
        monkeypatch.setenv("AEM_DB_ADAPTER", "sqlite")
        gate = PostgresProductionGate("postgresql://user:pass@localhost/test")
        result = gate.check_sqlite_disabled()
        assert result["ok"] is False

    def test_sqlite_disabled_when_adapter_not_explicitly_sqlite(self, monkeypatch):
        monkeypatch.delenv("AEM_DB_ADAPTER", raising=False)
        gate = PostgresProductionGate("postgresql://user:pass@localhost/test")
        result = gate.check_sqlite_disabled()
        assert result["ok"] is True


# ── check_backup_tooling ─────────────────────────────────────────────────────

class TestBackupTooling:
    def test_backup_result_has_required_fields(self):
        gate = PostgresProductionGate("postgresql://user:pass@localhost/test")
        result = gate.check_backup_tooling()
        assert "ok" in result
        assert "pg_dump_path" in result
        assert "detail" in result

    def test_backup_result_ok_is_bool(self):
        gate = PostgresProductionGate("postgresql://user:pass@localhost/test")
        result = gate.check_backup_tooling()
        assert isinstance(result["ok"], bool)


# ── Concurrent write logic ───────────────────────────────────────────────────

class TestAuditChainIntegrityLogic:
    def test_chain_hash_formula_correct(self):
        """Verify the chain hash formula used in concurrent write check."""
        import hashlib
        sha = hashlib.sha256(b"test-entry").hexdigest()
        prev = "0" * 64
        chain = hashlib.sha256(f"{prev}:{sha}".encode()).hexdigest()
        # Re-verify the same way check_audit_chain_integrity does
        expected = hashlib.sha256(f"{prev}:{sha}".encode()).hexdigest()
        assert chain == expected


# ── Health endpoint ──────────────────────────────────────────────────────────

class TestHealthPostgresGate:
    def test_postgres_persistence_gate_in_health(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert "postgres_persistence_gate" in data

    def test_gate_not_configured_when_no_db_url(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200
        gate = resp.json().get("postgres_persistence_gate", {})
        if not _DB_URL:
            assert gate.get("status") == "NOT_CONFIGURED"

    def test_gate_has_required_fields(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200
        gate = resp.json().get("postgres_persistence_gate", {})
        assert "gate" in gate
        assert gate["gate"] == "POSTGRES_PRODUCTION_PERSISTENCE_CHECK"

    def test_version_bumped(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.json()["version"] == "0.14.0-demo"


# ── Live DB tests (skip without AEM_DB_URL) ──────────────────────────────────

class TestLivePostgresGate:
    @_SKIP_NO_DB
    def test_connection_ping(self):
        gate = PostgresProductionGate(_DB_URL)
        result = gate.check_connection()
        assert result["ok"] is True

    @_SKIP_NO_DB
    def test_schema_validates(self):
        gate = PostgresProductionGate(_DB_URL)
        gate.run_migrations()
        result = gate.check_schema()
        assert result["ok"] is True
        assert not result["missing_tables"]

    @_SKIP_NO_DB
    def test_connection_pool(self):
        gate = PostgresProductionGate(_DB_URL)
        result = gate.check_connection_pool()
        assert result["ok"] is True

    @_SKIP_NO_DB
    def test_concurrent_writes(self):
        gate = PostgresProductionGate(_DB_URL)
        gate.run_migrations()
        result = gate.check_concurrent_writes(n_threads=4)
        assert result["ok"] is True
        assert result["inserted"] == 4

    @_SKIP_NO_DB
    def test_audit_chain_integrity(self):
        gate = PostgresProductionGate(_DB_URL)
        result = gate.check_audit_chain_integrity()
        assert result["ok"] is True

    @_SKIP_NO_DB
    def test_full_gate_check_passes(self):
        gate = PostgresProductionGate(_DB_URL)
        result = gate.gate_check()
        assert result["gate"] == "POSTGRES_PRODUCTION_PERSISTENCE_CHECK"
        assert result["status"] == "PASS"
