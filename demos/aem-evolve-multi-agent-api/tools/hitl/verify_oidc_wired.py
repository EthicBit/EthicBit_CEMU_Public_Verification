#!/usr/bin/env python3
"""
verify_oidc_wired.py — v1.8.0 OIDC dual-path HITL wiring check.

Checks:
  C-01  _oidc_key_pair is initialized (not None)
  C-02  _OIDC_POLICY has required fields (issuer, audience, approver_registry)
  C-03  GET /oidc/jwks returns 200 with RS256 key
  C-04  OIDC JWT approve returns 200 (valid token)
  C-05  HMAC hex approve still returns 200 (backwards-compatible)
  C-06  OIDC token with wrong sub returns 403
  C-07  OIDC token with wrong event_id returns 403
  C-08  OIDC token for unregistered sub returns 403
  C-09  OIDC token replay returns 409
  C-10  GET /health shows hitl_oidc_path=ENABLED

Expected output: OIDC_WIRED_VERIFICATION=PASS (10/10)
"""
from __future__ import annotations

import hashlib
import hmac as _hmac
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
_TOOLS_PATH = str(_DEMO_ROOT / "tools")
if _TOOLS_PATH not in sys.path:
    sys.path.insert(0, _TOOLS_PATH)

os.environ.setdefault("AEM_LOG_LEVEL", "WARNING")

from fastapi.testclient import TestClient  # noqa: E402
import main as _main  # noqa: E402

_INITIATOR_KEY = "demo-initiator-key-001"
_APPROVER_KEY  = "demo-approver-key-001"
_OBSERVER_KEY  = "demo-observer-key-001"
_HITL_SECRET   = "ethicbit-hitl-demo-secret-v1.4"
_HITL_APPROVER = "approver-001"


def _make_hmac_token(approver_id: str, event_id: str) -> str:
    ts_floor = math.floor(time.time() / 60)
    payload = f"{approver_id}:{event_id}:{ts_floor}".encode()
    return _hmac.new(_HITL_SECRET.encode(), payload, hashlib.sha256).hexdigest()


def _make_oidc_token(approver_id: str, event_id: str) -> str:
    from hitl.oidc_token_generator import generate_token
    kp = _main._oidc_key_pair
    policy = _main._OIDC_POLICY
    return generate_token(
        kp, sub=approver_id, event_id=event_id,
        issuer=policy.get("issuer", "https://hitl.ethicbit.internal"),
        audience=policy.get("audience", "aem-evolve-hitl"),
    )


def _tid() -> str:
    return f"ow-{uuid.uuid4().hex[:12]}"


def _start_and_get_event_id(client) -> tuple[str, str]:
    tid = _tid()
    client.post("/start", json={"thread_id": tid}, headers={"X-API-Key": _INITIATOR_KEY})
    rec = client.get(f"/receipt/{tid}", headers={"X-API-Key": _OBSERVER_KEY}).json()
    return tid, rec.get("event_id", "")


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

    # C-01 OIDC key pair initialized
    record("C-01-oidc-key-pair-initialized", _main._oidc_key_pair is not None)

    # C-02 OIDC policy has required fields
    policy = _main._OIDC_POLICY
    required = {"issuer", "audience", "approver_registry"}
    missing = required - set(policy.keys())
    record("C-02-oidc-policy-required-fields", not missing,
           f"missing={missing or 'none'}")

    with TestClient(_main.app, raise_server_exceptions=True) as client:
        # C-03 GET /oidc/jwks
        r = client.get("/oidc/jwks")
        jwks = r.json() if r.status_code == 200 else {}
        keys = jwks.get("keys", [])
        record("C-03-jwks-endpoint-rs256", r.status_code == 200 and bool(keys)
               and keys[0].get("alg") == "RS256",
               f"status={r.status_code} keys={len(keys)}")

        # C-04 OIDC JWT approve → 200
        tid, event_id = _start_and_get_event_id(client)
        if event_id:
            token = _make_oidc_token(_HITL_APPROVER, event_id)
            r = client.post("/approve",
                            json={"thread_id": tid, "decision": "approve",
                                  "hitl_token": token, "hitl_approver_id": _HITL_APPROVER},
                            headers={"X-API-Key": _APPROVER_KEY})
            record("C-04-oidc-approve-200", r.status_code == 200,
                   f"status={r.status_code}")
        else:
            record("C-04-oidc-approve-200", False, "no event_id")

        # C-05 HMAC hex approve still → 200
        tid2, eid2 = _start_and_get_event_id(client)
        if eid2:
            token2 = _make_hmac_token(_HITL_APPROVER, eid2)
            r = client.post("/approve",
                            json={"thread_id": tid2, "decision": "approve",
                                  "hitl_token": token2, "hitl_approver_id": _HITL_APPROVER},
                            headers={"X-API-Key": _APPROVER_KEY})
            record("C-05-hmac-still-works-200", r.status_code == 200,
                   f"status={r.status_code}")
        else:
            record("C-05-hmac-still-works-200", False, "no event_id")

        # C-06 OIDC wrong sub → 403
        tid3, eid3 = _start_and_get_event_id(client)
        if eid3:
            token3 = _make_oidc_token(_HITL_APPROVER, eid3)
            r = client.post("/approve",
                            json={"thread_id": tid3, "decision": "approve",
                                  "hitl_token": token3, "hitl_approver_id": "wrong-approver"},
                            headers={"X-API-Key": _APPROVER_KEY})
            record("C-06-oidc-wrong-sub-403", r.status_code == 403,
                   f"status={r.status_code}")
        else:
            record("C-06-oidc-wrong-sub-403", False, "no event_id")

        # C-07 OIDC wrong event_id → 403
        tid4, eid4 = _start_and_get_event_id(client)
        if eid4:
            token4 = _make_oidc_token(_HITL_APPROVER, "wrong-event-xyz")
            r = client.post("/approve",
                            json={"thread_id": tid4, "decision": "approve",
                                  "hitl_token": token4, "hitl_approver_id": _HITL_APPROVER},
                            headers={"X-API-Key": _APPROVER_KEY})
            record("C-07-oidc-wrong-event-403", r.status_code == 403,
                   f"status={r.status_code}")
        else:
            record("C-07-oidc-wrong-event-403", False, "no event_id")

        # C-08 OIDC unregistered sub → 403
        tid5, eid5 = _start_and_get_event_id(client)
        if eid5:
            token5 = _make_oidc_token("unregistered-attacker-999", eid5)
            r = client.post("/approve",
                            json={"thread_id": tid5, "decision": "approve",
                                  "hitl_token": token5, "hitl_approver_id": "unregistered-attacker-999"},
                            headers={"X-API-Key": _APPROVER_KEY})
            record("C-08-oidc-unregistered-sub-403", r.status_code == 403,
                   f"status={r.status_code}")
        else:
            record("C-08-oidc-unregistered-sub-403", False, "no event_id")

        # C-09 OIDC token replay → 409
        tid6, eid6 = _start_and_get_event_id(client)
        if eid6:
            token6 = _make_oidc_token(_HITL_APPROVER, eid6)
            _main._mark_token_used(token6, eid6, _HITL_APPROVER, _main.db_adapter)
            r = client.post("/approve",
                            json={"thread_id": tid6, "decision": "approve",
                                  "hitl_token": token6, "hitl_approver_id": _HITL_APPROVER},
                            headers={"X-API-Key": _APPROVER_KEY})
            record("C-09-oidc-replay-409", r.status_code == 409,
                   f"status={r.status_code}")
        else:
            record("C-09-oidc-replay-409", False, "no event_id")

        # C-10 /health shows hitl_oidc_path=ENABLED
        r = client.get("/health")
        health = r.json() if r.status_code == 200 else {}
        oidc_path = health.get("hitl_oidc_path", "")
        record("C-10-health-oidc-enabled", oidc_path == "ENABLED",
               f"field={oidc_path!r}")

    return passed, len(checks), checks


def main() -> int:
    print("OIDC Wired HITL Verification — AEM-EVOLVE™ v1.8.0")
    print("=" * 52)
    passed, total, checks = run_checks()
    print()

    result = "PASS" if passed == total else "FAIL"
    report = {
        "component": "verify_oidc_wired",
        "version": "v1.8",
        "checks_passed": passed,
        "checks_total": total,
        "result": result,
        "non_claims": [
            "OIDC key pair is locally generated — not a real IdP.",
            "JWKS is served in-process — not a real OIDC provider endpoint.",
            "Production requires external OIDC provider (Okta, Auth0, Keycloak).",
        ],
        "checks": checks,
    }

    out_dir = Path(__file__).resolve().parents[4] / "assurance" / "evolve-multi-agent" / "v1_8"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "oidc_wired_report.json").write_text(json.dumps(report, indent=2))

    print(f"OIDC_WIRED_VERIFICATION={result}  ({passed}/{total})")
    return 0 if result == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
