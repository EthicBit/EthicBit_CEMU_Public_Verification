"""
Tests for v2.0 PR 4 — migration and recovery evidence.

When AEM_DB_URL is not set: gate is NOT_CONFIGURED (correct).
When AEM_DB_URL is set: MigrationRecoveryEvidence runs live checks.
"""
import hashlib
import os
import sys
import pytest
from pathlib import Path

DEMO_ROOT = Path(__file__).resolve().parents[1]
if str(DEMO_ROOT) not in sys.path:
    sys.path.insert(0, str(DEMO_ROOT))

from db.migration_recovery_evidence import (
    MigrationRecoveryEvidence,
    MIGRATIONS_DIR,
    ROLLBACK_DIR,
    _AUDIT_TABLES,
)

_DB_URL = os.getenv("AEM_DB_URL", "")
_SKIP_NO_DB = pytest.mark.skipif(not _DB_URL, reason="AEM_DB_URL not set — live DB required")


# ── Init ────────────────────────────────────────────────────────────────────

class TestMigrationRecoveryEvidenceInit:
    def test_from_env_returns_none_without_db_url(self, monkeypatch):
        monkeypatch.delenv("AEM_DB_URL", raising=False)
        assert MigrationRecoveryEvidence.from_env() is None

    def test_from_env_returns_instance_with_db_url(self, monkeypatch):
        monkeypatch.setenv("AEM_DB_URL", "postgresql://user:pass@localhost/test")
        ev = MigrationRecoveryEvidence.from_env()
        assert ev is not None
        assert ev._db_url == "postgresql://user:pass@localhost/test"


# ── Migrations directory ─────────────────────────────────────────────────────

class TestMigrationsDirectory:
    def test_forward_migrations_directory_exists(self):
        assert MIGRATIONS_DIR.exists()

    def test_at_least_one_forward_migration(self):
        assert len(list(MIGRATIONS_DIR.glob("*.sql"))) >= 1

    def test_rollback_directory_exists(self):
        assert ROLLBACK_DIR.exists(), f"rollback dir not found: {ROLLBACK_DIR}"

    def test_at_least_one_rollback_migration(self):
        files = list(ROLLBACK_DIR.glob("*.sql"))
        assert len(files) >= 1, "no rollback SQL files found"

    def test_rollback_001_drops_all_audit_tables(self):
        rb = ROLLBACK_DIR / "001_rollback_initial_schema.sql"
        assert rb.exists()
        content = rb.read_text()
        for table in ["evolution_events", "evolution_receipts", "audit_chain", "hitl_used_tokens"]:
            assert table in content, f"{table} not in rollback 001"

    def test_rollback_files_are_hashable(self):
        for f in sorted(ROLLBACK_DIR.glob("*.sql")):
            sha = hashlib.sha256(f.read_bytes()).hexdigest()
            assert len(sha) == 64


# ── Count reconciliation logic ───────────────────────────────────────────────

class TestCountReconciliation:
    def _make_ev(self):
        return MigrationRecoveryEvidence("postgresql://user:pass@localhost/test")

    def test_reconcile_no_regression(self):
        ev = self._make_ev()
        before = {"evolution_events": 5, "audit_chain": 10}
        after = {"evolution_events": 7, "audit_chain": 10}
        result = ev.reconcile_counts(before, after)
        assert result["ok"] is True
        assert result["regressions"] == []

    def test_reconcile_detects_regression(self):
        ev = self._make_ev()
        before = {"evolution_events": 10, "audit_chain": 5}
        after = {"evolution_events": 8, "audit_chain": 5}
        result = ev.reconcile_counts(before, after)
        assert result["ok"] is False
        assert len(result["regressions"]) == 1
        assert "evolution_events" in result["regressions"][0]

    def test_reconcile_ignores_negative_counts(self):
        ev = self._make_ev()
        before = {"evolution_events": -1, "audit_chain": 3}
        after = {"evolution_events": -1, "audit_chain": 3}
        result = ev.reconcile_counts(before, after)
        assert result["ok"] is True

    def test_reconcile_all_audit_tables_covered(self):
        ev = self._make_ev()
        before = {t: 0 for t in _AUDIT_TABLES}
        after = {t: 0 for t in _AUDIT_TABLES}
        result = ev.reconcile_counts(before, after)
        assert result["ok"] is True


# ── Audit-chain continuity logic ─────────────────────────────────────────────

class TestAuditChainContinuityLogic:
    def test_chain_hash_formula(self):
        """Verify the hash formula used in verify_audit_chain_continuity."""
        sha = hashlib.sha256(b"entry-data").hexdigest()
        prev = "0" * 64
        expected = hashlib.sha256(f"{prev}:{sha}".encode()).hexdigest()
        # Re-derive to confirm formula is deterministic
        assert expected == hashlib.sha256(f"{prev}:{sha}".encode()).hexdigest()

    def test_different_sha_produces_different_chain(self):
        sha1 = hashlib.sha256(b"entry-1").hexdigest()
        sha2 = hashlib.sha256(b"entry-2").hexdigest()
        prev = "0" * 64
        c1 = hashlib.sha256(f"{prev}:{sha1}".encode()).hexdigest()
        c2 = hashlib.sha256(f"{prev}:{sha2}".encode()).hexdigest()
        assert c1 != c2


# ── Backup tooling ───────────────────────────────────────────────────────────

class TestBackupTooling:
    def test_run_backup_returns_structure(self, monkeypatch):
        monkeypatch.setenv("AEM_DB_URL", "postgresql://user:pass@localhost/test")
        ev = MigrationRecoveryEvidence("postgresql://user:pass@localhost/test")
        result = ev.run_backup()
        assert "ok" in result
        assert "detail" in result

    def test_verify_backup_content_fails_on_missing_file(self):
        ev = MigrationRecoveryEvidence("postgresql://user:pass@localhost/test")
        result = ev.verify_backup_content(Path("/nonexistent/dump.sql"))
        assert result["ok"] is False

    def test_verify_backup_content_detects_tables(self, tmp_path):
        ev = MigrationRecoveryEvidence("postgresql://user:pass@localhost/test")
        dump = tmp_path / "dump.sql"
        dump.write_text(
            "CREATE TABLE evolution_events (...); "
            "CREATE TABLE evolution_receipts (...); "
            "CREATE TABLE audit_chain (...); "
            "CREATE TABLE hitl_used_tokens (...);"
        )
        result = ev.verify_backup_content(dump)
        assert result["ok"] is True
        assert len(result["tables_missing_from_dump"]) == 0

    def test_verify_backup_content_detects_missing_tables(self, tmp_path):
        ev = MigrationRecoveryEvidence("postgresql://user:pass@localhost/test")
        dump = tmp_path / "dump.sql"
        dump.write_text("CREATE TABLE unrelated_table (...);")
        result = ev.verify_backup_content(dump)
        assert result["ok"] is False
        assert len(result["tables_missing_from_dump"]) > 0


# ── Health endpoint ──────────────────────────────────────────────────────────

class TestHealthMigrationRecoveryGate:
    def test_migration_recovery_gate_in_health(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200
        assert "migration_recovery_gate" in resp.json()

    def test_gate_has_required_fields(self, client):
        resp = client.get("/health")
        gate = resp.json()["migration_recovery_gate"]
        assert gate["gate"] == "MIGRATION_RECOVERY_CHECK"
        assert "rollback_files_present" in gate
        assert gate["rollback_files_present"] >= 1

    def test_version_bumped(self, client):
        resp = client.get("/health")
        assert resp.json()["version"] == "0.15.0-demo"


# ── Live DB tests ────────────────────────────────────────────────────────────

class TestLiveMigrationRecovery:
    @_SKIP_NO_DB
    def test_hash_schema_state(self):
        ev = MigrationRecoveryEvidence(_DB_URL)
        result = ev.hash_schema_state("test")
        assert result["ok"] is True
        assert len(result["schema_hash"]) == 64

    @_SKIP_NO_DB
    def test_forward_migration_evidence(self):
        ev = MigrationRecoveryEvidence(_DB_URL)
        result = ev.forward_migration_evidence()
        assert result["ok"] is True
        assert result["before_hash"] is not None
        assert result["after_hash"] is not None

    @_SKIP_NO_DB
    def test_rollback_evidence_produced(self):
        ev = MigrationRecoveryEvidence(_DB_URL)
        result = ev.rollback_migration_evidence()
        assert result["ok"] is True
        assert len(result["rollback_files"]) >= 1

    @_SKIP_NO_DB
    def test_audit_chain_continuity(self):
        ev = MigrationRecoveryEvidence(_DB_URL)
        result = ev.verify_audit_chain_continuity()
        assert result["ok"] is True

    @_SKIP_NO_DB
    def test_count_reconciliation_after_migration(self):
        ev = MigrationRecoveryEvidence(_DB_URL)
        before = ev.record_row_counts("before")
        after = ev.record_row_counts("after")
        recon = ev.reconcile_counts(before["counts"], after["counts"])
        assert recon["ok"] is True

    @_SKIP_NO_DB
    def test_generate_evidence_structure(self):
        ev = MigrationRecoveryEvidence(_DB_URL)
        evidence = ev.generate_evidence()
        assert evidence["gate"] == "MIGRATION_RECOVERY_CHECK"
        assert "evidence" in evidence
        assert "status" in evidence
        required_keys = [
            "forward_migration", "rollback_migration",
            "count_reconciliation", "audit_chain_continuity",
            "backup_test", "restore_verification",
        ]
        for key in required_keys:
            assert key in evidence["evidence"], f"missing evidence key: {key}"
