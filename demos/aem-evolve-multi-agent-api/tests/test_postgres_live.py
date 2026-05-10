"""
Fast-path pytest tests for v1.9.0 PostgreSQL live integration.
All tests are skipped automatically if AEM_DB_URL is not set.
"""
import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

_DB_URL = os.environ.get("AEM_DB_URL", "")
_SKIP = pytest.mark.skipif(not _DB_URL, reason="AEM_DB_URL not set — Postgres live tests skipped")

_TEST_TABLE = "aem_v1_9_live_test"


@_SKIP
class TestPostgresLive:
    @pytest.fixture(autouse=True)
    def _adapter(self):
        from db_adapter import PostgresAdapter
        self.adapter = PostgresAdapter(_DB_URL)
        yield
        try:
            self.adapter.execute_write(f"DROP TABLE IF EXISTS {_TEST_TABLE}")
            self.adapter.commit()
        except Exception:
            pass
        self.adapter.close()

    def test_psycopg2_importable(self):
        import psycopg2  # noqa: F401

    def test_connection_reachable(self):
        rows = self.adapter.execute("SELECT 1")
        assert rows == [(1,)]

    def test_ping_returns_true(self):
        assert self.adapter.ping() is True

    def test_create_table(self):
        self.adapter.execute_write(
            f"CREATE TABLE IF NOT EXISTS {_TEST_TABLE} (id SERIAL PRIMARY KEY, val TEXT)"
        )
        self.adapter.commit()

    def test_insert_and_select(self):
        self.adapter.execute_write(
            f"CREATE TABLE IF NOT EXISTS {_TEST_TABLE} (id SERIAL PRIMARY KEY, val TEXT)"
        )
        self.adapter.execute_write(
            f"INSERT INTO {_TEST_TABLE} (val) VALUES (%s)", ("v1.9-live-test",)
        )
        self.adapter.commit()
        rows = self.adapter.execute(f"SELECT val FROM {_TEST_TABLE}")
        assert any(r[0] == "v1.9-live-test" for r in rows)

    def test_audit_chain_table_creation(self):
        from main import init_audit_tables
        init_audit_tables(self.adapter)
        rows = self.adapter.execute(
            "SELECT tablename FROM pg_tables WHERE schemaname='public'"
        )
        table_names = {r[0] for r in rows}
        assert "audit_chain" in table_names
        assert "evolution_events" in table_names

    def test_audit_chain_insert_and_read(self):
        import hashlib
        from datetime import datetime, timezone
        from main import init_audit_tables, GENESIS_HASH
        init_audit_tables(self.adapter)
        sha = hashlib.sha256(b"test-entry").hexdigest()
        chain = hashlib.sha256(f"{GENESIS_HASH}:{sha}".encode()).hexdigest()
        self.adapter.execute_write(
            "INSERT INTO audit_chain "
            "(entry_type, entry_id, entry_sha256, prev_chain_hash, chain_hash, timestamp_utc) "
            "VALUES (%s, %s, %s, %s, %s, %s)",
            ("test", "test-id-1", sha, GENESIS_HASH, chain,
             datetime.now(timezone.utc).isoformat()),
        )
        self.adapter.commit()
        rows = self.adapter.execute(
            "SELECT chain_hash FROM audit_chain WHERE entry_id = %s", ("test-id-1",)
        )
        assert rows[0][0] == chain

    def test_hitl_used_tokens_table(self):
        from main import init_audit_tables
        from datetime import datetime, timezone
        init_audit_tables(self.adapter)
        self.adapter.execute_write(
            "INSERT INTO hitl_used_tokens (token_hash, event_id, approver_id, used_at) "
            "VALUES (%s, %s, %s, %s) ON CONFLICT DO NOTHING",
            ("abc123", "evt-1", "approver-001", datetime.now(timezone.utc).isoformat()),
        )
        self.adapter.commit()
        rows = self.adapter.execute(
            "SELECT token_hash FROM hitl_used_tokens WHERE event_id = %s", ("evt-1",)
        )
        assert rows[0][0] == "abc123"

    def test_cleanup(self):
        self.adapter.execute_write(f"DROP TABLE IF EXISTS {_TEST_TABLE}")
        self.adapter.commit()
        rows = self.adapter.execute(
            f"SELECT tablename FROM pg_tables WHERE tablename = '{_TEST_TABLE}'"
        )
        assert rows == []
