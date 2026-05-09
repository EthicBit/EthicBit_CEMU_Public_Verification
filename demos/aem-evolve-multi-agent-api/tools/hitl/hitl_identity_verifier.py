#!/usr/bin/env python3
"""
hitl_identity_verifier.py — HMAC-SHA256 time-bounded HITL identity verification.

Checks:
  C-01  Policy file loads and contains required fields
  C-02  Token generator produces a non-empty hex string
  C-03  Token verifies correctly for a known-good (approver, event, timestamp)
  C-04  Token with wrong approver_id is rejected
  C-05  Token with wrong event_id is rejected
  C-06  Token with wrong secret is rejected
  C-07  Expired token (> TTL minutes old) is rejected
  C-08  Token generated at current minute floor verifies (live round-trip)
  C-09  Approver not in registry is rejected
  C-10  Policy non-claims are present in the policy document

Expected output: HITL_IDENTITY_VERIFICATION=PASS
"""

from __future__ import annotations

import hashlib
import hmac
import json
import math
import os
import sys
import time
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_POLICY_FILE = _HERE / "HITL_IDENTITY_POLICY.json"
_SECRET_ENV = "ETHICBIT_HITL_SHARED_SECRET"
_DEMO_SECRET = "ethicbit-hitl-demo-secret-v1.4"


def _load_policy() -> dict:
    return json.loads(_POLICY_FILE.read_text())


def _get_secret() -> str:
    return os.environ.get(_SECRET_ENV) or _DEMO_SECRET


def _make_token(approver_id: str, event_id: str, secret: str, ts_floor: int) -> str:
    payload = f"{approver_id}:{event_id}:{ts_floor}".encode()
    return hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()


def verify_token(
    token: str,
    approver_id: str,
    event_id: str,
    secret: str,
    policy: dict,
    now: float | None = None,
) -> tuple[bool, str]:
    """
    Verify *token* against approver_id, event_id, secret, and policy TTL.

    Returns (ok, reason).
    """
    now = now if now is not None else time.time()
    ttl_minutes = policy.get("token_ttl_minutes", 10)
    registry_ids = {a["approver_id"] for a in policy.get("approver_registry", [])}

    if approver_id not in registry_ids:
        return False, f"approver_id {approver_id!r} not in registry"

    ts_now_floor = math.floor(now / 60)
    for offset in range(ttl_minutes + 1):
        ts_floor = ts_now_floor - offset
        expected = _make_token(approver_id, event_id, secret, ts_floor)
        if hmac.compare_digest(token, expected):
            if offset > ttl_minutes:
                return False, f"token expired (offset={offset} minutes > TTL={ttl_minutes})"
            return True, f"verified at offset={offset} minutes"

    return False, "token does not match any valid time window"


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

    # C-01 Policy file loads
    try:
        policy = _load_policy()
        required = {"policy_id", "token_ttl_minutes", "approver_registry", "non_claims"}
        missing = required - set(policy.keys())
        record("C-01-policy-loads", not missing, f"missing={missing or 'none'}")
    except Exception as exc:
        record("C-01-policy-loads", False, str(exc))
        policy = {"token_ttl_minutes": 10, "approver_registry": [], "non_claims": []}

    secret = _get_secret()
    approver = "approver-001"
    event = "evt-test-001"
    now = time.time()
    ts_floor = math.floor(now / 60)

    # C-02 Token generator produces non-empty hex
    token = _make_token(approver, event, secret, ts_floor)
    record("C-02-token-generated", bool(token) and all(c in "0123456789abcdef" for c in token),
           f"len={len(token)}")

    # C-03 Correct token verifies
    ok, reason = verify_token(token, approver, event, secret, policy, now)
    record("C-03-correct-token-verifies", ok, reason)

    # C-04 Wrong approver rejected
    wrong_approver_token = _make_token("attacker-999", event, secret, ts_floor)
    ok, reason = verify_token(wrong_approver_token, "attacker-999", event, secret, policy, now)
    record("C-04-wrong-approver-rejected", not ok, reason)

    # C-05 Wrong event rejected
    wrong_event_token = _make_token(approver, "wrong-event", secret, ts_floor)
    ok, _ = verify_token(wrong_event_token, approver, event, secret, policy, now)
    record("C-05-wrong-event-rejected", not ok)

    # C-06 Wrong secret rejected
    token_good = _make_token(approver, event, secret, ts_floor)
    ok, _ = verify_token(token_good, approver, event, "wrong-secret", policy, now)
    record("C-06-wrong-secret-rejected", not ok)

    # C-07 Expired token rejected (timestamp > TTL minutes in past)
    ttl = policy.get("token_ttl_minutes", 10)
    old_ts_floor = ts_floor - (ttl + 2)
    expired_token = _make_token(approver, event, secret, old_ts_floor)
    ok, reason = verify_token(expired_token, approver, event, secret, policy, now)
    record("C-07-expired-token-rejected", not ok, reason)

    # C-08 Live round-trip at current minute floor
    live_token = _make_token(approver, event, secret, math.floor(time.time() / 60))
    ok, reason = verify_token(live_token, approver, event, secret, policy)
    record("C-08-live-roundtrip", ok, reason)

    # C-09 Approver not in registry rejected
    unregistered_token = _make_token("unregistered-999", event, secret, ts_floor)
    ok, reason = verify_token(unregistered_token, "unregistered-999", event, secret, policy, now)
    record("C-09-unregistered-approver-rejected", not ok, reason)

    # C-10 Non-claims present
    non_claims = policy.get("non_claims", [])
    record("C-10-non-claims-present", len(non_claims) >= 2,
           f"count={len(non_claims)}")

    return passed, len(checks), checks


def main() -> int:
    print("HITL Identity Verifier")
    print("=" * 44)
    passed, total, checks = run_checks()
    print()

    result = "PASS" if passed == total else "FAIL"
    report = {
        "component": "hitl_identity_verifier",
        "version": "v1.4",
        "checks_passed": passed,
        "checks_total": total,
        "result": result,
        "token_format": "HMAC-SHA256(secret, approver_id + ':' + event_id + ':' + timestamp_floor_minutes)",
        "non_claims": [
            "HITL identity is not enterprise IAM.",
            "Shared secret is demo-grade.",
            "HSM-backed identity requires external IdP integration.",
        ],
        "checks": checks,
    }

    out_dir = Path(__file__).resolve().parent.parent.parent.parent.parent / "assurance" / "evolve-multi-agent" / "v1_4"
    out_dir.mkdir(parents=True, exist_ok=True)
    report_path = out_dir / "hitl_identity_report.json"
    report_path.write_text(json.dumps(report, indent=2))

    print(f"HITL_IDENTITY_VERIFICATION={result}  ({passed}/{total})")
    return 0 if result == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
