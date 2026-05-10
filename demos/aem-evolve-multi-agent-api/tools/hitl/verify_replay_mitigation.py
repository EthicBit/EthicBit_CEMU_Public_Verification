#!/usr/bin/env python3
"""
verify_replay_mitigation.py — v1.7.0 HITL replay-attack mitigation check.

Checks:
  C-01  hitl_used_tokens table exists in DB schema
  C-02  _is_token_used returns False for unused token
  C-03  _mark_token_used persists token hash
  C-04  _is_token_used returns True after mark
  C-05  Different event_id not counted as used
  C-06  _mark_token_used is idempotent (no duplicate key error)
  C-07  POST /approve with pre-marked token returns 409
  C-08  409 response body contains 'replay'
  C-09  Fresh token for same session that has been approved → 400 (no pending)
  C-10  GET /health shows hitl_replay_mitigation field

Expected output: REPLAY_MITIGATION_VERIFICATION=PASS (10/10)
"""
from __future__ import annotations

import hashlib
import hmac
import json
import math
import os
import sys
import time
import uuid
from pathlib import Path

_DEMO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_DEMO_ROOT) not in sys.path:
    sys.path.insert(0, str(_DEMO_ROOT))

os.environ.setdefault("AEM_LOG_LEVEL", "WARNING")

from fastapi.testclient import TestClient  # noqa: E402
import main as _main  # noqa: E402
from main import _is_token_used, _mark_token_used, init_audit_tables  # noqa: E402
from db_adapter import SQLiteAdapter  # noqa: E402

_HITL_SECRET = "ethicbit-hitl-demo-secret-v1.4"
_HITL_APPROVER = "approver-001"
_INITIATOR_KEY = "demo-initiator-key-001"
_APPROVER_KEY = "demo-approver-key-001"
_OBSERVER_KEY = "demo-observer-key-001"


def _make_hitl_token(approver_id: str, event_id: str) -> str:
    ts_floor = math.floor(time.time() / 60)
    payload = f"{approver_id}:{event_id}:{ts_floor}".encode()
    return hmac.new(_HITL_SECRET.encode(), payload, hashlib.sha256).hexdigest()


def run_checks() -> tuple[int, int, list[dict]]:
    checks: list[dict] = []
    passed = 0

    def record(name: str, ok: bool, detail: str = "") -> None:
        nonlocal passed
        status = "PASS" if ok else "FAIL"
        checks.append({"check": name, "status": status, "detail": detail})
        if ok:
            passed += 1
        print(f"  {status}  {name}" + (f"  — {detail}" if detail else ""))

    adapter = SQLiteAdapter(":memory:")
    init_audit_tables(adapter)

    # C-01 hitl_used_tokens table exists
    try:
        rows = adapter.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='hitl_used_tokens'"
        )
        record("C-01-hitl-used-tokens-table-exists", bool(rows))
    except Exception as exc:
        record("C-01-hitl-used-tokens-table-exists", False, str(exc))

    # C-02 unused token → False
    try:
        result = _is_token_used("test-token-abc", "evt-001", adapter)
        record("C-02-unused-token-returns-false", result is False, f"result={result}")
    except Exception as exc:
        record("C-02-unused-token-returns-false", False, str(exc))

    # C-03 _mark_token_used persists hash
    try:
        _mark_token_used("test-token-abc", "evt-001", "approver-001", adapter)
        token_hash = hashlib.sha256("test-token-abc".encode()).hexdigest()
        rows = adapter.execute(
            "SELECT token_hash FROM hitl_used_tokens WHERE event_id = 'evt-001'"
        )
        record("C-03-mark-persists-hash", bool(rows) and rows[0][0] == token_hash,
               f"stored={rows[0][0][:16] if rows else 'none'}...")
    except Exception as exc:
        record("C-03-mark-persists-hash", False, str(exc))

    # C-04 is_used returns True after mark
    try:
        result = _is_token_used("test-token-abc", "evt-001", adapter)
        record("C-04-used-after-mark", result is True, f"result={result}")
    except Exception as exc:
        record("C-04-used-after-mark", False, str(exc))

    # C-05 different event_id not considered used
    try:
        result = _is_token_used("test-token-abc", "evt-999", adapter)
        record("C-05-different-event-not-used", result is False, f"result={result}")
    except Exception as exc:
        record("C-05-different-event-not-used", False, str(exc))

    # C-06 idempotent mark
    try:
        _mark_token_used("test-token-abc", "evt-001", "approver-001", adapter)
        _mark_token_used("test-token-abc", "evt-001", "approver-001", adapter)
        record("C-06-mark-idempotent", True)
    except Exception as exc:
        record("C-06-mark-idempotent", False, str(exc))

    # C-07 / C-08 / C-09 / C-10 — via TestClient
    with TestClient(_main.app, raise_server_exceptions=True) as client:
        tid = f"rm-{uuid.uuid4().hex[:12]}"
        client.post("/start", json={"thread_id": tid},
                    headers={"X-API-Key": _INITIATOR_KEY})
        rec = client.get(f"/receipt/{tid}", headers={"X-API-Key": _OBSERVER_KEY}).json()
        event_id = rec.get("event_id", "")

        # C-07 pre-marked token → 409
        if event_id:
            token = _make_hitl_token(_HITL_APPROVER, event_id)
            _mark_token_used(token, event_id, _HITL_APPROVER, _main.db_adapter)
            r = client.post("/approve",
                            json={"thread_id": tid, "decision": "approve",
                                  "hitl_token": token, "hitl_approver_id": _HITL_APPROVER},
                            headers={"X-API-Key": _APPROVER_KEY})
            record("C-07-replay-returns-409", r.status_code == 409,
                   f"status={r.status_code}")
        else:
            record("C-07-replay-returns-409", False, "no event_id")

        # C-08 response contains 'replay'
        if event_id:
            record("C-08-409-body-mentions-replay", "replay" in r.text.lower(),
                   f"body={r.text[:80]}")
        else:
            record("C-08-409-body-mentions-replay", False, "no event_id")

        # C-09 approved session → 400 (no pending) not 409
        tid2 = f"rm2-{uuid.uuid4().hex[:12]}"
        import math as _math
        client.post("/start", json={"thread_id": tid2},
                    headers={"X-API-Key": _INITIATOR_KEY})
        rec2 = client.get(f"/receipt/{tid2}", headers={"X-API-Key": _OBSERVER_KEY}).json()
        eid2 = rec2.get("event_id", "")
        if eid2:
            tok2 = _make_hitl_token(_HITL_APPROVER, eid2)
            r2 = client.post("/approve",
                             json={"thread_id": tid2, "decision": "approve",
                                   "hitl_token": tok2, "hitl_approver_id": _HITL_APPROVER},
                             headers={"X-API-Key": _APPROVER_KEY})
            # Now try again — no pending, should be 400 not 409
            tok3 = _make_hitl_token(_HITL_APPROVER, eid2)
            r3 = client.post("/approve",
                             json={"thread_id": tid2, "decision": "approve",
                                   "hitl_token": tok3, "hitl_approver_id": _HITL_APPROVER},
                             headers={"X-API-Key": _APPROVER_KEY})
            record("C-09-no-pending-is-400-not-409", r3.status_code == 400,
                   f"status={r3.status_code}")
        else:
            record("C-09-no-pending-is-400-not-409", False, "no event_id2")

        # C-10 /health shows replay mitigation field
        r = client.get("/health")
        health = r.json() if r.status_code == 200 else {}
        replay_field = health.get("hitl_replay_mitigation", "")
        record("C-10-health-shows-replay-mitigation", bool(replay_field),
               f"field={replay_field!r}")

    return passed, len(checks), checks


def main() -> int:
    print("HITL Replay Mitigation Verification — AEM-EVOLVE™ v1.7.0")
    print("=" * 58)
    passed, total, checks = run_checks()
    print()

    result = "PASS" if passed == total else "FAIL"
    report = {
        "component": "verify_replay_mitigation",
        "version": "v1.7",
        "checks_passed": passed,
        "checks_total": total,
        "result": result,
        "non_claims": [
            "Nonce store is DB-backed but SQLite is not tamper-proof.",
            "Token hash is SHA256 — not a formal nonce protocol.",
            "Server restart clears in-memory state but DB persists nonces.",
        ],
        "checks": checks,
    }

    out_dir = Path(__file__).resolve().parents[4] / "assurance" / "evolve-multi-agent" / "v1_7"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "replay_mitigation_report.json").write_text(json.dumps(report, indent=2))

    print(f"REPLAY_MITIGATION_VERIFICATION={result}  ({passed}/{total})")
    return 0 if result == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
