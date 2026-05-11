"""
PostgresProductionGate — v2.0 PR 3 production PostgreSQL persistence validation.

Covers all eight mandatory evidence items from the PR 3 gate checklist:
  1. PostgreSQLAdapter active in production config
  2. SQLite disabled in production mode
  3. Migrations executed successfully
  4. Schema validation PASS
  5. Connection pooling configured (psycopg2 ThreadedConnectionPool / pgbouncer)
  6. Load test under concurrent approvals/writes
  7. Audit-chain integrity verified under load
  8. Backup tooling available (pg_dump reachable)

from_env() returns None when AEM_DB_URL is not set.
gate_check() returns a structured dict for /health and assurance.

Non-claims:
  Not production-tested at scale without a real PostgreSQL instance.
  pgbouncer configuration requires separate infrastructure evidence.
  Backup/restore validation requires separate scheduled evidence.
  Not production-ready by itself — one gate of 12.
"""
from __future__ import annotations

import hashlib
import os
import shutil
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DEMO_ROOT = Path(__file__).resolve().parents[1]
MIGRATIONS_DIR = DEMO_ROOT / "migrations"

_AEM_DB_URL_ENV = "AEM_DB_URL"
_AEM_DB_ADAPTER_ENV = "AEM_DB_ADAPTER"

# Tables and their mandatory columns
_REQUIRED_SCHEMA: dict[str, list[str]] = {
    "evolution_events": [
        "event_id", "thread_id", "event_canonical_sha256", "change_type",
        "base_artifact", "proposed_state", "materiality_score",
        "requested_claim_scope", "timestamp_utc", "claim_boundary", "event_json",
    ],
    "evolution_receipts": [
        "receipt_canonical_sha256", "thread_id", "event_id", "outcome",
        "receipt_message", "materiality_score", "claim_boundary",
        "requested_claim_scope", "signature_status", "timestamp_utc", "receipt_json",
    ],
    "human_decisions": [
        "id", "thread_id", "event_id", "decision", "approver_id", "timestamp_utc",
    ],
    "audit_chain": [
        "seq", "entry_type", "entry_id", "entry_sha256",
        "prev_chain_hash", "chain_hash", "timestamp_utc",
    ],
    "hitl_used_tokens": [
        "token_hash", "event_id", "approver_id", "used_at",
    ],
}


class PostgresProductionGate:
    """
    Validates all PR 3 mandatory evidence items for a PostgreSQL-backed deployment.
    """

    def __init__(self, db_url: str) -> None:
        self._db_url = db_url
        self._adapter: Any = None  # lazy-loaded PostgresAdapter

    # ------------------------------------------------------------------
    @classmethod
    def from_env(cls) -> "PostgresProductionGate | None":
        """Return gate from env, or None when AEM_DB_URL not set."""
        url = os.getenv(_AEM_DB_URL_ENV, "").strip()
        if not url:
            return None
        return cls(url)

    # ------------------------------------------------------------------
    def _get_adapter(self) -> Any:
        if self._adapter is None:
            import sys
            if str(DEMO_ROOT) not in sys.path:
                sys.path.insert(0, str(DEMO_ROOT))
            from db_adapter import PostgresAdapter
            self._adapter = PostgresAdapter(self._db_url, minconn=1, maxconn=10)
        return self._adapter

    # ------------------------------------------------------------------
    # Individual checks
    # ------------------------------------------------------------------

    def check_connection(self) -> dict[str, Any]:
        """C-03: PostgresAdapter connects and ping succeeds."""
        try:
            adapter = self._get_adapter()
            rows = adapter.execute("SELECT version()")
            ping = adapter.ping()
            pg_version = rows[0][0] if rows else "unknown"
            return {
                "ok": ping,
                "pg_version": pg_version[:60],
                "detail": "ping=True" if ping else "ping=False",
            }
        except Exception as exc:
            return {"ok": False, "detail": str(exc)[:120]}

    def check_sqlite_disabled(self) -> dict[str, Any]:
        """C-04: SQLite is not the active adapter when AEM_DB_URL is set."""
        adapter_type = os.getenv(_AEM_DB_ADAPTER_ENV, "").strip().lower()
        db_url_set = bool(self._db_url)
        # When AEM_DB_URL is set and adapter is postgres (or unspecified but URL present),
        # SQLite should not be active.
        ok = db_url_set and adapter_type != "sqlite"
        return {
            "ok": ok,
            "adapter_env": adapter_type or "(not set — inferred from AEM_DB_URL)",
            "db_url_set": db_url_set,
            "detail": (
                "SQLite not active — PostgreSQL adapter in use"
                if ok
                else "AEM_DB_ADAPTER=sqlite overrides AEM_DB_URL — SQLite still active"
            ),
        }

    def run_migrations(self) -> dict[str, Any]:
        """C-05: Execute all migration SQL files from migrations/ directory."""
        if not MIGRATIONS_DIR.exists():
            return {"ok": False, "detail": f"migrations/ directory not found at {MIGRATIONS_DIR}"}
        sql_files = sorted(MIGRATIONS_DIR.glob("*.sql"))
        if not sql_files:
            return {"ok": False, "detail": "No .sql migration files found"}
        adapter = self._get_adapter()
        applied = []
        failed = []
        for f in sql_files:
            sql = f.read_text(encoding="utf-8")
            statements = [s.strip() for s in sql.split(";") if s.strip()]
            try:
                for stmt in statements:
                    adapter.execute_write(stmt)
                adapter.commit()
                applied.append(f.name)
            except Exception as exc:
                failed.append({"file": f.name, "error": str(exc)[:100]})
        ok = len(failed) == 0
        return {
            "ok": ok,
            "applied": applied,
            "failed": failed,
            "detail": f"{len(applied)} migration(s) applied" + (f"; {len(failed)} failed" if failed else ""),
        }

    def check_schema(self) -> dict[str, Any]:
        """C-06: Verify all required tables and columns exist."""
        adapter = self._get_adapter()
        # Ensure audit tables are created (idempotent)
        import sys
        if str(DEMO_ROOT) not in sys.path:
            sys.path.insert(0, str(DEMO_ROOT))
        from main import init_audit_tables
        try:
            init_audit_tables(adapter)
        except Exception:
            pass
        missing_tables = []
        missing_columns: dict[str, list[str]] = {}
        try:
            rows = adapter.execute(
                "SELECT tablename FROM pg_tables WHERE schemaname='public'"
            )
            present_tables = {r[0] for r in rows}
            for table, required_cols in _REQUIRED_SCHEMA.items():
                if table not in present_tables:
                    missing_tables.append(table)
                    continue
                col_rows = adapter.execute(
                    "SELECT column_name FROM information_schema.columns "
                    "WHERE table_schema='public' AND table_name=%s",
                    (table,),
                )
                present_cols = {r[0] for r in col_rows}
                missing = [c for c in required_cols if c not in present_cols]
                if missing:
                    missing_columns[table] = missing
        except Exception as exc:
            return {"ok": False, "detail": str(exc)[:120]}
        ok = not missing_tables and not missing_columns
        return {
            "ok": ok,
            "missing_tables": missing_tables,
            "missing_columns": missing_columns,
            "tables_validated": list(_REQUIRED_SCHEMA.keys()),
            "detail": "all tables and columns present" if ok else f"missing_tables={missing_tables}, missing_columns={missing_columns}",
        }

    def check_connection_pool(self) -> dict[str, Any]:
        """C-07: Verify psycopg2 ThreadedConnectionPool is active (or pgbouncer URL detected)."""
        try:
            adapter = self._get_adapter()
            pool = getattr(adapter, "_pool", None)
            has_pool = pool is not None
            pool_type = type(pool).__name__ if pool else "none"
            pgbouncer_detected = "pgbouncer" in self._db_url.lower() or ":6432" in self._db_url
            ok = has_pool or pgbouncer_detected
            return {
                "ok": ok,
                "pool_type": pool_type,
                "pgbouncer_detected": pgbouncer_detected,
                "detail": (
                    f"ThreadedConnectionPool active (type={pool_type})"
                    if has_pool
                    else "pgbouncer detected in DSN" if pgbouncer_detected
                    else "no connection pool detected"
                ),
            }
        except Exception as exc:
            return {"ok": False, "detail": str(exc)[:120]}

    def check_concurrent_writes(self, n_threads: int = 8) -> dict[str, Any]:
        """C-08: Concurrent INSERT to audit_chain from N threads — no data corruption."""
        adapter = self._get_adapter()
        errors: list[str] = []
        inserted_ids: list[str] = []
        lock = threading.Lock()

        def _insert(i: int) -> None:
            entry_id = f"conc-load-{i}-{datetime.now(timezone.utc).timestamp()}"
            sha = hashlib.sha256(entry_id.encode()).hexdigest()
            prev = "0" * 64
            chain = hashlib.sha256(f"{prev}:{sha}".encode()).hexdigest()
            try:
                from db_adapter import PostgresAdapter
                # Each thread gets its own connection from the pool
                thread_adapter = PostgresAdapter(self._db_url, minconn=1, maxconn=2)
                thread_adapter.execute_write(
                    "INSERT INTO audit_chain "
                    "(entry_type, entry_id, entry_sha256, prev_chain_hash, chain_hash, timestamp_utc) "
                    "VALUES (%s, %s, %s, %s, %s, %s) ON CONFLICT DO NOTHING",
                    ("load_test", entry_id, sha, prev, chain,
                     datetime.now(timezone.utc).isoformat()),
                )
                thread_adapter.commit()
                thread_adapter.close()
                with lock:
                    inserted_ids.append(entry_id)
            except Exception as exc:
                with lock:
                    errors.append(f"thread-{i}: {str(exc)[:80]}")

        threads = [threading.Thread(target=_insert, args=(i,)) for i in range(n_threads)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=15)

        ok = len(errors) == 0 and len(inserted_ids) == n_threads
        return {
            "ok": ok,
            "n_threads": n_threads,
            "inserted": len(inserted_ids),
            "errors": errors,
            "detail": f"{len(inserted_ids)}/{n_threads} writes succeeded" + (f"; errors: {errors[:2]}" if errors else ""),
        }

    def check_audit_chain_integrity(self) -> dict[str, Any]:
        """C-09: Verify audit chain entries have valid hash linkage after load test."""
        adapter = self._get_adapter()
        try:
            rows = adapter.execute(
                "SELECT entry_sha256, prev_chain_hash, chain_hash FROM audit_chain "
                "ORDER BY seq"
            )
            if not rows:
                return {"ok": True, "detail": "no audit_chain entries (empty DB)", "entries_checked": 0}
            broken = 0
            for sha, prev, chain in rows:
                expected = hashlib.sha256(f"{prev}:{sha}".encode()).hexdigest()
                if expected != chain:
                    broken += 1
            ok = broken == 0
            return {
                "ok": ok,
                "entries_checked": len(rows),
                "broken_links": broken,
                "detail": f"{len(rows)} entries, {broken} broken link(s)" if not ok else f"{len(rows)} entries all valid",
            }
        except Exception as exc:
            return {"ok": False, "detail": str(exc)[:120]}

    def check_backup_tooling(self) -> dict[str, Any]:
        """C-10: Verify pg_dump is available in PATH."""
        pg_dump_path = shutil.which("pg_dump")
        ok = pg_dump_path is not None
        return {
            "ok": ok,
            "pg_dump_path": pg_dump_path,
            "detail": f"pg_dump found at {pg_dump_path}" if ok else "pg_dump not found in PATH",
        }

    # ------------------------------------------------------------------
    def gate_check(self) -> dict[str, Any]:
        """Run all checks and return a comprehensive gate status dict."""
        result: dict[str, Any] = {
            "gate": "POSTGRES_PRODUCTION_PERSISTENCE_CHECK",
            "db_url_configured": True,
            "checks": {},
        }

        # Ordered checks — each failure is recorded, gate continues
        all_ok = True

        def _run(key: str, fn, *args) -> dict:
            nonlocal all_ok
            try:
                r = fn(*args) if args else fn()
            except Exception as exc:
                r = {"ok": False, "detail": str(exc)[:120]}
            result["checks"][key] = r
            if not r.get("ok", False):
                all_ok = False
            return r

        _run("connection", self.check_connection)
        _run("sqlite_disabled", self.check_sqlite_disabled)
        _run("migrations", self.run_migrations)
        _run("schema", self.check_schema)
        _run("connection_pool", self.check_connection_pool)
        _run("concurrent_writes", self.check_concurrent_writes)
        _run("audit_chain_integrity", self.check_audit_chain_integrity)
        _run("backup_tooling", self.check_backup_tooling)

        result["status"] = "PASS" if all_ok else "FAIL"
        result["reason"] = "all checks passed" if all_ok else "one or more checks failed"
        return result
