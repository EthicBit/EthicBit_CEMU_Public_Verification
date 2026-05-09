#!/usr/bin/env python3
"""
verify_signed_receipts.py — Verifies that the AEM-EVOLVE™ API actually signs
events and receipts end-to-end (v1.6.0 critical gap closure).

Checks:
  C-01  API server imports without error
  C-02  _signing_provider is initialized (not None)
  C-03  _SIGNING_STATUS is not NOT_SIGNED_DEMO
  C-04  POST /start → event has signature_hex field
  C-05  POST /start → event signature_status is not NOT_SIGNED_DEMO
  C-06  POST /start → event signature_hex is a valid hex string (128 chars, Ed25519)
  C-07  GET /receipt → receipt has signature_hex field
  C-08  GET /receipt → receipt signature_status is not NOT_SIGNED_DEMO
  C-09  signature is verifiable with public key from provider
  C-10  /health reports actual signing_status (not hardcoded DEMO_SIGNED_ED25519)

Expected output: SIGNED_RECEIPTS_VERIFICATION=PASS (10/10)
"""
from __future__ import annotations

import json
import math
import os
import sys
import time
import uuid
from pathlib import Path

_DEMO_ROOT = Path(__file__).resolve().parents[2]
if str(_DEMO_ROOT) not in sys.path:
    sys.path.insert(0, str(_DEMO_ROOT))

os.environ.setdefault("AEM_LOG_LEVEL", "WARNING")


def main() -> int:
    passed = 0
    failed = 0

    def ok(label: str) -> None:
        nonlocal passed
        passed += 1
        print(f"  PASS  {label}")

    def fail(label: str, detail: str = "") -> None:
        nonlocal failed
        failed += 1
        print(f"  FAIL  {label}" + (f" — {detail}" if detail else ""))

    print("AEM-EVOLVE™ v1.6 Signed Receipts Verification")
    print("=" * 52)

    # C-01 Import
    try:
        import main as _main
        ok("C-01  API server imports without error")
    except Exception as exc:
        fail("C-01  API server imports without error", str(exc))
        print(f"\nSIGNED_RECEIPTS_VERIFICATION=FAIL ({passed}/{passed+failed})")
        return 1

    # C-02 signing_provider not None
    provider = getattr(_main, "_signing_provider", None)
    if provider is not None:
        ok("C-02  _signing_provider initialized")
    else:
        fail("C-02  _signing_provider initialized", "_signing_provider is None")

    # C-03 _SIGNING_STATUS is real
    sig_status = getattr(_main, "_SIGNING_STATUS", "NOT_SIGNED_DEMO")
    if sig_status and sig_status != "NOT_SIGNED_DEMO":
        ok(f"C-03  _SIGNING_STATUS={sig_status!r} (real)")
    else:
        fail("C-03  _SIGNING_STATUS real", f"got {sig_status!r}")

    # C-04..C-09 require TestClient
    from fastapi.testclient import TestClient

    initiator_key = "demo-initiator-key-001"
    observer_key = "demo-observer-key-001"
    tid = f"vsr-{uuid.uuid4().hex[:14]}"

    with TestClient(_main.app, raise_server_exceptions=True) as client:
        r = client.post("/start", json={"thread_id": tid},
                        headers={"X-API-Key": initiator_key})
        if r.status_code != 200:
            fail("C-04  /start event signature_hex", f"start failed: {r.status_code}")
            fail("C-05  /start event signature_status", "skipped")
            fail("C-06  /start event signature_hex hex format", "skipped")
            fail("C-07  /receipt signature_hex", "skipped")
            fail("C-08  /receipt signature_status", "skipped")
            fail("C-09  signature verifiable", "skipped")
        else:
            # Retrieve event from /audit
            audit = client.get(f"/audit/{tid}", headers={"X-API-Key": observer_key}).json()
            events = audit.get("events", [])
            event = events[0] if events else {}

            # C-04
            if "signature_hex" in event:
                ok("C-04  /start event has signature_hex")
            else:
                fail("C-04  /start event has signature_hex", f"keys={list(event.keys())[:8]}")

            # C-05
            ev_sig_status = event.get("signature_status", "NOT_SIGNED_DEMO")
            if ev_sig_status and ev_sig_status != "NOT_SIGNED_DEMO":
                ok(f"C-05  event signature_status={ev_sig_status!r}")
            else:
                fail("C-05  event signature_status real", f"got {ev_sig_status!r}")

            # C-06 — Ed25519 sig is 64 bytes = 128 hex chars
            sig_hex = event.get("signature_hex", "")
            if len(sig_hex) == 128 and all(c in "0123456789abcdef" for c in sig_hex.lower()):
                ok("C-06  event signature_hex is valid 128-char hex (Ed25519)")
            else:
                fail("C-06  event signature_hex format", f"len={len(sig_hex)}")

            # C-07 receipt
            receipt_r = client.get(f"/receipt/{tid}", headers={"X-API-Key": observer_key})
            receipt = receipt_r.json() if receipt_r.status_code == 200 else {}
            if "signature_hex" in receipt:
                ok("C-07  /receipt has signature_hex")
            else:
                fail("C-07  /receipt has signature_hex", f"keys={list(receipt.keys())[:8]}")

            # C-08
            rec_sig_status = receipt.get("signature_status", "NOT_SIGNED_DEMO")
            if rec_sig_status and rec_sig_status != "NOT_SIGNED_DEMO":
                ok(f"C-08  receipt signature_status={rec_sig_status!r}")
            else:
                fail("C-08  receipt signature_status real", f"got {rec_sig_status!r}")

            # C-09 verify signature with provider's public key
            try:
                sha_hex = event.get("event_canonical_sha256", "")
                sig_bytes = bytes.fromhex(sig_hex)
                msg_bytes = sha_hex.encode()
                if provider and provider.verify(msg_bytes, sig_bytes):
                    ok("C-09  event signature verifiable with provider public key")
                else:
                    fail("C-09  event signature verifiable", "verify() returned False")
            except Exception as exc:
                fail("C-09  event signature verifiable", str(exc))

        # C-10 /health
        health = client.get("/health").json()
        h_sig_status = health.get("signing_status", "DEMO_SIGNED_ED25519")
        if h_sig_status and h_sig_status != "DEMO_SIGNED_ED25519":
            ok(f"C-10  /health signing_status={h_sig_status!r} (real)")
        else:
            fail("C-10  /health signing_status real", f"got {h_sig_status!r}")

    total = passed + failed
    overall = "PASS" if failed == 0 else "FAIL"
    print(f"\nSIGNED_RECEIPTS_VERIFICATION={overall} ({passed}/{total})")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
