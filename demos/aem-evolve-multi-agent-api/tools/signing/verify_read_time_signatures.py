#!/usr/bin/env python3
"""
verify_read_time_signatures.py — v1.7.0 read-time signature verification check.

Checks:
  C-01  _verify_artifact_signature is importable
  C-02  Signed event produces signature_verified=True
  C-03  Signed receipt produces signature_verified=True
  C-04  Tampered signature_hex produces signature_verified=False
  C-05  Missing signature fields produce signature_verified=False with note
  C-06  GET /receipt returns signature_verified field
  C-07  GET /event returns signature_verified for each event
  C-08  GET /audit events carry signature_verified=True
  C-09  GET /audit receipts carry signature_verified=True
  C-10  signature_verification_note is present on all verified artifacts

Expected output: READ_TIME_SIG_VERIFICATION=PASS (10/10)
"""
from __future__ import annotations

import json
import math
import os
import sys
import time
import uuid
import hmac
import hashlib
from pathlib import Path

_DEMO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_DEMO_ROOT) not in sys.path:
    sys.path.insert(0, str(_DEMO_ROOT))

os.environ.setdefault("AEM_LOG_LEVEL", "WARNING")

from fastapi.testclient import TestClient  # noqa: E402
import main as _main  # noqa: E402
from main import (  # noqa: E402
    _verify_artifact_signature,
    create_evolution_event,
    evaluate_evolution_gate,
    init_audit_tables,
)
from db_adapter import SQLiteAdapter  # noqa: E402

_HITL_SECRET = "ethicbit-hitl-demo-secret-v1.4"
_HITL_APPROVER = "approver-001"
_INITIATOR_KEY = "demo-initiator-key-001"
_OBSERVER_KEY = "demo-observer-key-001"


def _make_hitl_token(approver_id: str, event_id: str) -> str:
    ts_floor = math.floor(time.time() / 60)
    payload = f"{approver_id}:{event_id}:{ts_floor}".encode()
    return hmac.new(_HITL_SECRET.encode(), payload, hashlib.sha256).hexdigest()


def _make_event_payload(score: float) -> dict:
    return {
        "event_id": f"EVO-TEST-{score}-{uuid.uuid4().hex[:8]}",
        "materiality_score": score,
        "requested_claim_scope": "RESEARCH_SUPPORT",
        "claim_boundary": {
            "research_support_only": True,
            "clinical_claimed": False,
            "diagnostic_claimed": False,
            "regulatory_approval_claimed": False,
            "third_party_binding": False,
        },
        "event_canonical_sha256": "abc123",
    }


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

    # C-01 importable
    try:
        assert callable(_verify_artifact_signature)
        record("C-01-verify-artifact-importable", True)
    except Exception as exc:
        record("C-01-verify-artifact-importable", False, str(exc))

    # C-02 signed event verifies
    try:
        evt = create_evolution_event("CONFIG_UPDATE", "art", "st", 55.0, adapter, "t-rv-01")
        v = _verify_artifact_signature(evt)
        record("C-02-event-verified-at-read", v.get("signature_verified") is True,
               f"verified={v.get('signature_verified')}")
    except Exception as exc:
        record("C-02-event-verified-at-read", False, str(exc))

    # C-03 signed receipt verifies
    try:
        event = _make_event_payload(50.0)
        receipt = evaluate_evolution_gate(event, adapter, "t-rv-02")
        v = _verify_artifact_signature(receipt)
        record("C-03-receipt-verified-at-read", v.get("signature_verified") is True,
               f"verified={v.get('signature_verified')}")
    except Exception as exc:
        record("C-03-receipt-verified-at-read", False, str(exc))

    # C-04 tampered signature rejected
    try:
        evt = create_evolution_event("CONFIG_UPDATE", "art", "st", 55.0, adapter, "t-rv-03")
        tampered = dict(evt)
        tampered["signature_hex"] = "00" * 64
        v = _verify_artifact_signature(tampered)
        record("C-04-tampered-sig-rejected", v.get("signature_verified") is False,
               f"verified={v.get('signature_verified')}")
    except Exception as exc:
        record("C-04-tampered-sig-rejected", False, str(exc))

    # C-05 missing signature fields → False + note
    try:
        artifact = {"event_canonical_sha256": "abc", "outcome": "PASS"}
        v = _verify_artifact_signature(artifact)
        record("C-05-missing-sig-fields", v.get("signature_verified") is False
               and "missing" in v.get("signature_verification_note", ""),
               f"note={v.get('signature_verification_note')!r}")
    except Exception as exc:
        record("C-05-missing-sig-fields", False, str(exc))

    # C-06 / C-07 / C-08 / C-09 / C-10 — via TestClient
    with TestClient(_main.app, raise_server_exceptions=True) as client:
        tid = f"rv-{uuid.uuid4().hex[:12]}"
        client.post("/start", json={"thread_id": tid},
                    headers={"X-API-Key": _INITIATOR_KEY})

        # C-06 GET /receipt has signature_verified
        r = client.get(f"/receipt/{tid}", headers={"X-API-Key": _OBSERVER_KEY})
        rec = r.json() if r.status_code == 200 else {}
        record("C-06-receipt-endpoint-verified", rec.get("signature_verified") is True,
               f"verified={rec.get('signature_verified')}")

        # C-07 GET /event has signature_verified on each
        r = client.get(f"/event/{tid}", headers={"X-API-Key": _OBSERVER_KEY})
        evts = (r.json() if r.status_code == 200 else {}).get("events", [])
        all_ok = bool(evts) and all(e.get("signature_verified") is True for e in evts)
        record("C-07-event-endpoint-verified", all_ok,
               f"count={len(evts)} all_verified={all_ok}")

        # C-08 GET /audit events have signature_verified
        r = client.get(f"/audit/{tid}", headers={"X-API-Key": _OBSERVER_KEY})
        audit = r.json() if r.status_code == 200 else {}
        aevts = audit.get("events", [])
        all_evts_ok = bool(aevts) and all(e.get("signature_verified") is True for e in aevts)
        record("C-08-audit-events-verified", all_evts_ok,
               f"count={len(aevts)}")

        # C-09 GET /audit receipts have signature_verified
        arecs = audit.get("receipts", [])
        all_recs_ok = bool(arecs) and all(r.get("signature_verified") is True for r in arecs)
        record("C-09-audit-receipts-verified", all_recs_ok,
               f"count={len(arecs)}")

        # C-10 verification_note present
        all_have_note = (
            bool(aevts) and all("signature_verification_note" in e for e in aevts)
            and bool(arecs) and all("signature_verification_note" in r for r in arecs)
        )
        record("C-10-verification-note-present", all_have_note)

    return passed, len(checks), checks


def main() -> int:
    print("Read-Time Signature Verification — AEM-EVOLVE™ v1.7.0")
    print("=" * 56)
    passed, total, checks = run_checks()
    print()

    result = "PASS" if passed == total else "FAIL"
    report = {
        "component": "verify_read_time_signatures",
        "version": "v1.7",
        "checks_passed": passed,
        "checks_total": total,
        "result": result,
        "non_claims": [
            "Verification uses the same in-process key — not an independent verifier.",
            "Does not cover HSM-backed key custody.",
        ],
        "checks": checks,
    }

    out_dir = Path(__file__).resolve().parents[4] / "assurance" / "evolve-multi-agent" / "v1_7"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "read_time_sig_report.json").write_text(json.dumps(report, indent=2))

    print(f"READ_TIME_SIG_VERIFICATION={result}  ({passed}/{total})")
    return 0 if result == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
