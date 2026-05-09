#!/usr/bin/env python3
"""
e2e_api_test.py — End-to-end integration test for AEM-EVOLVE™ API v1.6.0.

Tests the full governance flow via FastAPI TestClient:
  start → status → receipt → approve (with HITL token) → audit → chain/verify

Checks:
  C-01  POST /start returns 200, sets status=awaiting_human_approval
  C-02  GET /status shows human_approval_needed=True
  C-03  GET /receipt shows SCOPE_LIMITED outcome with signature_hex
  C-04  Receipt signature_status is not NOT_SIGNED_DEMO
  C-05  POST /approve without HITL token returns 400
  C-06  POST /approve with invalid HITL token returns 403
  C-07  POST /approve with valid HITL token returns 200
  C-08  GET /audit shows events, receipts, and human_decisions
  C-09  GET /chain/verify returns PASS and entries_checked >= 3
  C-10  GET /health shows actual signing_status (not DEMO_SIGNED_ED25519)

Expected output: E2E_API_VERIFICATION=PASS (10/10)
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

_INITIATOR_KEY = "demo-initiator-key-001"
_APPROVER_KEY = "demo-approver-key-001"
_OBSERVER_KEY = "demo-observer-key-001"
_HITL_SECRET = "ethicbit-hitl-demo-secret-v1.4"
_HITL_APPROVER = "approver-001"


def _make_hitl_token(approver_id: str, event_id: str, secret: str = _HITL_SECRET) -> str:
    ts_floor = math.floor(time.time() / 60)
    payload = f"{approver_id}:{event_id}:{ts_floor}".encode()
    return hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()


def _tid() -> str:
    return f"e2e-{uuid.uuid4().hex[:16]}"


def run_e2e() -> tuple[int, int, list[str]]:
    passed = 0
    failed = 0
    errors: list[str] = []

    def ok(label: str) -> None:
        nonlocal passed
        passed += 1
        print(f"  PASS  {label}")

    def fail(label: str, detail: str) -> None:
        nonlocal failed
        failed += 1
        errors.append(f"{label}: {detail}")
        print(f"  FAIL  {label} — {detail}")

    with TestClient(_main.app, raise_server_exceptions=True) as client:
        tid = _tid()

        # C-01 POST /start
        r = client.post("/start", json={"thread_id": tid},
                        headers={"X-API-Key": _INITIATOR_KEY})
        if r.status_code == 200 and r.json().get("status") == "awaiting_human_approval":
            ok("C-01  POST /start → awaiting_human_approval")
        else:
            fail("C-01  POST /start", f"status={r.status_code} body={r.text[:120]}")

        # C-02 GET /status
        r = client.get(f"/status/{tid}", headers={"X-API-Key": _OBSERVER_KEY})
        body = r.json() if r.status_code == 200 else {}
        if r.status_code == 200 and body.get("human_approval_needed") is True:
            ok("C-02  GET /status → human_approval_needed=True")
        else:
            fail("C-02  GET /status", f"status={r.status_code} han={body.get('human_approval_needed')}")

        # C-03 GET /receipt
        r = client.get(f"/receipt/{tid}", headers={"X-API-Key": _OBSERVER_KEY})
        receipt = r.json() if r.status_code == 200 else {}
        event_id = receipt.get("event_id", "")
        if (r.status_code == 200
                and receipt.get("receipt_payload", {}).get("outcome") == "SCOPE_LIMITED"
                and "signature_hex" in receipt):
            ok("C-03  GET /receipt → SCOPE_LIMITED + signature_hex present")
        else:
            fail("C-03  GET /receipt", f"status={r.status_code} outcome={receipt.get('receipt_payload',{}).get('outcome')} sig={'signature_hex' in receipt}")

        # C-04 signature_status is real (not NOT_SIGNED_DEMO)
        sig_status = receipt.get("signature_status", "")
        if sig_status and sig_status != "NOT_SIGNED_DEMO":
            ok(f"C-04  Receipt signature_status={sig_status!r} (real)")
        else:
            fail("C-04  Receipt signature_status", f"got {sig_status!r}")

        # C-05 /approve without HITL token → 400
        r = client.post("/approve",
                        json={"thread_id": tid, "decision": "approve"},
                        headers={"X-API-Key": _APPROVER_KEY})
        if r.status_code == 400:
            ok("C-05  POST /approve without token → 400")
        else:
            fail("C-05  POST /approve without token", f"expected 400, got {r.status_code}")

        # C-06 /approve with invalid HITL token → 403
        r = client.post("/approve",
                        json={"thread_id": tid, "decision": "approve",
                              "hitl_token": "deadbeef" * 8, "hitl_approver_id": _HITL_APPROVER},
                        headers={"X-API-Key": _APPROVER_KEY})
        if r.status_code == 403:
            ok("C-06  POST /approve with invalid token → 403")
        else:
            fail("C-06  POST /approve with invalid token", f"expected 403, got {r.status_code}")

        # C-07 /approve with valid HITL token → 200
        if event_id:
            token = _make_hitl_token(_HITL_APPROVER, event_id)
            r = client.post("/approve",
                            json={"thread_id": tid, "decision": "approve",
                                  "hitl_token": token, "hitl_approver_id": _HITL_APPROVER},
                            headers={"X-API-Key": _APPROVER_KEY})
            if r.status_code == 200:
                ok("C-07  POST /approve with valid token → 200")
            else:
                fail("C-07  POST /approve with valid token", f"status={r.status_code} body={r.text[:120]}")
        else:
            fail("C-07  POST /approve", "no event_id available (C-03 failed)")

        # C-08 GET /audit
        r = client.get(f"/audit/{tid}", headers={"X-API-Key": _OBSERVER_KEY})
        audit = r.json() if r.status_code == 200 else {}
        if (r.status_code == 200
                and len(audit.get("events", [])) >= 1
                and len(audit.get("receipts", [])) >= 1
                and len(audit.get("human_decisions", [])) >= 1):
            ok("C-08  GET /audit → events + receipts + human_decisions")
        else:
            fail("C-08  GET /audit", f"status={r.status_code} e={len(audit.get('events',[]))} r={len(audit.get('receipts',[]))} d={len(audit.get('human_decisions',[]))}")

        # C-09 GET /chain/verify
        r = client.get("/chain/verify", headers={"X-API-Key": _OBSERVER_KEY})
        chain = r.json() if r.status_code == 200 else {}
        if r.status_code == 200 and chain.get("status") == "PASS" and chain.get("entries_checked", 0) >= 3:
            ok(f"C-09  GET /chain/verify → PASS ({chain.get('entries_checked')} entries)")
        else:
            fail("C-09  GET /chain/verify", f"status={r.status_code} chain_status={chain.get('status')} entries={chain.get('entries_checked')}")

        # C-10 GET /health signing_status
        r = client.get("/health")
        health = r.json() if r.status_code == 200 else {}
        signing_status = health.get("signing_status", "")
        if signing_status and signing_status != "DEMO_SIGNED_ED25519":
            ok(f"C-10  GET /health signing_status={signing_status!r} (real)")
        else:
            fail("C-10  GET /health signing_status", f"got {signing_status!r}")

    return passed, failed, errors


if __name__ == "__main__":
    print("=" * 60)
    print("E2E API INTEGRATION TEST — AEM-EVOLVE™ v1.6.0")
    print("=" * 60)
    passed, failed, errors = run_e2e()
    total = passed + failed
    print("=" * 60)
    if failed == 0:
        print(f"E2E_API_VERIFICATION=PASS ({total}/{total})")
        sys.exit(0)
    else:
        print(f"E2E_API_VERIFICATION=FAIL ({passed}/{total})")
        for e in errors:
            print(f"  ERROR: {e}")
        sys.exit(1)
