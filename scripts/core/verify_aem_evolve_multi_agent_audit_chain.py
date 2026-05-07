#!/usr/bin/env python3
"""
Standalone tamper-evident audit chain verifier for AEM-EVOLVE Multi-Agent Governance API.

Connects directly to the SQLite demo database and walks every row in
audit_chain, recomputing chain_hash = SHA256(prev_chain_hash:entry_sha256)
and confirming prev_chain_hash links match.

Any discrepancy is reported as TAMPER_DETECTED.

Usage:
  python verify_aem_evolve_multi_agent_audit_chain.py [db_path]

  db_path defaults to demos/aem-evolve-multi-agent-api/ethicbit_demo.db

Exit codes:
  0  PASS — chain intact
  1  TAMPER_DETECTED or ERROR
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DB = ROOT / "demos" / "aem-evolve-multi-agent-api" / "ethicbit_demo.db"
GENESIS_HASH = "0" * 64


def _compute_chain_hash(prev: str, entry_sha256: str) -> str:
    return hashlib.sha256(f"{prev}:{entry_sha256}".encode()).hexdigest()


def verify(db_path: Path) -> int:
    if not db_path.exists():
        print(f"ERROR: database not found: {db_path}", file=sys.stderr)
        return 1

    conn = sqlite3.connect(str(db_path))
    try:
        cur = conn.cursor()
        try:
            cur.execute(
                "SELECT seq, entry_type, entry_id, entry_sha256, prev_chain_hash, chain_hash, timestamp_utc "
                "FROM audit_chain ORDER BY seq"
            )
        except sqlite3.OperationalError as exc:
            print(f"ERROR: audit_chain table not found — {exc}", file=sys.stderr)
            return 1

        rows = cur.fetchall()
    finally:
        conn.close()

    print("=== AEM-EVOLVE MULTI-AGENT API AUDIT CHAIN VERIFICATION ===")
    print(f"db_path          = {db_path}")
    print(f"entries_found    = {len(rows)}")
    print("")

    if not rows:
        print("AEM_EVOLVE_AUDIT_CHAIN_STATUS=EMPTY")
        print("NOTE: No entries yet — start the API and run /start to populate.")
        return 0

    errors: list[dict] = []
    expected_prev = GENESIS_HASH

    for seq, entry_type, entry_id, entry_sha256, prev_chain_hash, chain_hash, timestamp_utc in rows:
        recomputed = _compute_chain_hash(prev_chain_hash, entry_sha256)

        prev_ok = prev_chain_hash == expected_prev
        hash_ok = recomputed == chain_hash

        status = "OK" if (prev_ok and hash_ok) else "FAIL"
        print(f"  seq={seq:04d} type={entry_type:<20s} id={entry_id[:36]:<36s} {status}")

        if not prev_ok:
            errors.append({
                "seq": seq, "entry_id": entry_id,
                "error": "prev_chain_hash_mismatch",
                "expected": expected_prev, "got": prev_chain_hash,
            })
        if not hash_ok:
            errors.append({
                "seq": seq, "entry_id": entry_id,
                "error": "chain_hash_mismatch",
                "recomputed": recomputed, "stored": chain_hash,
            })

        expected_prev = chain_hash

    print("")
    head = rows[-1][5]
    print(f"head_chain_hash  = {head}")
    print(f"entries_checked  = {len(rows)}")

    if errors:
        print(f"\nERRORS ({len(errors)}):")
        print(json.dumps(errors, indent=2))
        print("\nAEM_EVOLVE_AUDIT_CHAIN_STATUS=TAMPER_DETECTED")
        print("NOTE: Hash-linked detection only. SQLite is demo storage — not tamper-proof.")
        return 1

    print("\nAEM_EVOLVE_AUDIT_CHAIN_STATUS=PASS")
    print("NOTE: Hash-linked detection only. SQLite is demo storage — not tamper-proof.")
    return 0


if __name__ == "__main__":
    db_path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_DB
    raise SystemExit(verify(db_path))
