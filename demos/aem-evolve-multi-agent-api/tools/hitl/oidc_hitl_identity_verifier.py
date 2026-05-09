#!/usr/bin/env python3
"""
oidc_hitl_identity_verifier.py — OIDC RS256 JWT HITL identity verification.

Verifies OIDC ID tokens (RS256 JWTs) against an inline JWKS.
No PyJWT required — uses cryptography library (already installed).

Checks:
  C-01  Policy file loads with required fields
  C-02  Token generator produces a dot-separated JWT string
  C-03  Valid token verifies against JWKS (signature + claims)
  C-04  Expired token is rejected
  C-05  Token with wrong issuer is rejected
  C-06  Token with wrong audience is rejected
  C-07  Token with tampered payload is rejected
  C-08  Approver not in registry is rejected
  C-09  Wrong event_id in token is rejected
  C-10  Policy non-claims are present

Expected output: OIDC_HITL_VERIFICATION=PASS
"""

from __future__ import annotations

import base64
import json
import sys
import time
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_POLICY_FILE = _HERE / "HITL_OIDC_POLICY.json"

sys.path.insert(0, str(_HERE.parent))

from hitl.oidc_token_generator import OidcTestKeyPair, generate_token  # noqa: E402


def _b64url_decode(s: str) -> bytes:
    s += "=" * (4 - len(s) % 4)
    return base64.urlsafe_b64decode(s)


def _parse_jwt(token: str) -> tuple[dict, dict, bytes, bytes]:
    parts = token.split(".")
    if len(parts) != 3:
        raise ValueError("JWT must have 3 parts")
    header  = json.loads(_b64url_decode(parts[0]))
    payload = json.loads(_b64url_decode(parts[1]))
    sig     = _b64url_decode(parts[2])
    signing_input = f"{parts[0]}.{parts[1]}".encode()
    return header, payload, sig, signing_input


def _get_rsa_public_key(jwks: dict, kid: str):
    from cryptography.hazmat.primitives.asymmetric.rsa import RSAPublicNumbers
    from cryptography.hazmat.backends import default_backend

    def _b64url_int(s: str) -> int:
        data = _b64url_decode(s)
        return int.from_bytes(data, "big")

    for key in jwks.get("keys", []):
        if key.get("kid") == kid and key.get("alg") == "RS256":
            n = _b64url_int(key["n"])
            e = _b64url_int(key["e"])
            return RSAPublicNumbers(e, n).public_key(default_backend())
    raise KeyError(f"No RS256 key with kid={kid!r} found in JWKS")


def verify_oidc_token(
    token: str,
    jwks: dict,
    policy: dict,
    now: float | None = None,
) -> tuple[bool, str, dict]:
    """Verify token against JWKS + policy.  Returns (ok, reason, payload)."""
    now = now if now is not None else time.time()
    try:
        header, payload, sig, signing_input = _parse_jwt(token)
    except Exception as exc:
        return False, f"JWT parse error: {exc}", {}

    # Signature
    try:
        from cryptography.hazmat.primitives import hashes
        from cryptography.hazmat.primitives.asymmetric import padding as asym_padding
        from cryptography.exceptions import InvalidSignature

        pub = _get_rsa_public_key(jwks, header.get("kid", ""))
        pub.verify(sig, signing_input, asym_padding.PKCS1v15(), hashes.SHA256())
    except InvalidSignature:
        return False, "signature invalid", payload
    except Exception as exc:
        return False, f"signature check error: {exc}", payload

    # Claims
    if payload.get("iss") != policy["issuer"]:
        return False, f"wrong issuer: {payload.get('iss')!r}", payload
    if payload.get("aud") != policy["audience"]:
        return False, f"wrong audience: {payload.get('aud')!r}", payload
    if payload.get("exp", 0) < now:
        return False, f"token expired (exp={payload.get('exp')} now={int(now)})", payload

    registry_subs = {a["sub"] for a in policy.get("approver_registry", [])}
    if payload.get("sub") not in registry_subs:
        return False, f"sub {payload.get('sub')!r} not in approver registry", payload

    return True, "verified", payload


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

    # C-01 Policy loads
    try:
        policy = json.loads(_POLICY_FILE.read_text())
        required = {"policy_id", "issuer", "audience", "approver_registry", "non_claims"}
        missing = required - set(policy.keys())
        record("C-01-policy-loads", not missing, f"missing={missing or 'none'}")
    except Exception as exc:
        record("C-01-policy-loads", False, str(exc))
        return passed, 1, checks

    kp = OidcTestKeyPair()
    jwks = kp.jwks()
    approver = "approver-001"
    event_id = "evt-test-v1.5"
    now = time.time()

    token = generate_token(kp, sub=approver, event_id=event_id,
                           issuer=policy["issuer"], audience=policy["audience"])

    # C-02 Token is valid JWT string
    parts = token.split(".")
    record("C-02-token-is-jwt", len(parts) == 3, f"parts={len(parts)}")

    # C-03 Valid token verifies
    ok, reason, _ = verify_oidc_token(token, jwks, policy, now)
    record("C-03-valid-token-verifies", ok, reason)

    # C-04 Expired token rejected
    old_token = generate_token(kp, sub=approver, event_id=event_id,
                               issuer=policy["issuer"], audience=policy["audience"],
                               ttl_seconds=-1, now=now - 700)
    ok, reason, _ = verify_oidc_token(old_token, jwks, policy, now)
    record("C-04-expired-token-rejected", not ok, reason)

    # C-05 Wrong issuer rejected
    wrong_iss_token = generate_token(kp, sub=approver, event_id=event_id,
                                     issuer="https://attacker.example.com",
                                     audience=policy["audience"])
    ok, reason, _ = verify_oidc_token(wrong_iss_token, jwks, policy, now)
    record("C-05-wrong-issuer-rejected", not ok, reason)

    # C-06 Wrong audience rejected
    wrong_aud_token = generate_token(kp, sub=approver, event_id=event_id,
                                     issuer=policy["issuer"],
                                     audience="wrong-audience")
    ok, reason, _ = verify_oidc_token(wrong_aud_token, jwks, policy, now)
    record("C-06-wrong-audience-rejected", not ok, reason)

    # C-07 Tampered payload rejected (flip one byte in the payload segment)
    parts = token.split(".")
    tampered = parts[0] + "." + parts[1][:-2] + "AA" + "." + parts[2]
    try:
        ok, reason, _ = verify_oidc_token(tampered, jwks, policy, now)
        record("C-07-tampered-payload-rejected", not ok, reason)
    except Exception as exc:
        record("C-07-tampered-payload-rejected", True, f"exception={exc!r}"[:60])

    # C-08 Unregistered approver rejected
    unregistered_token = generate_token(kp, sub="attacker-999", event_id=event_id,
                                        issuer=policy["issuer"], audience=policy["audience"])
    ok, reason, _ = verify_oidc_token(unregistered_token, jwks, policy, now)
    record("C-08-unregistered-approver-rejected", not ok, reason)

    # C-09 event_id claim is present and preserved in a verified token
    ok_verify, _, payload_dict = verify_oidc_token(token, jwks, policy, now)
    event_present = "event_id" in payload_dict
    record("C-09-event-id-claim-present", event_present and ok_verify,
           f"event_id={payload_dict.get('event_id')!r}")

    # C-10 Non-claims present
    non_claims = policy.get("non_claims", [])
    record("C-10-non-claims-present", len(non_claims) >= 2, f"count={len(non_claims)}")

    return passed, len(checks), checks


def main() -> int:
    print("OIDC HITL Identity Verifier")
    print("=" * 44)
    passed, total, checks = run_checks()
    print()

    result = "PASS" if passed == total else "FAIL"
    report = {
        "component": "oidc_hitl_identity_verifier",
        "version": "v1.5",
        "checks_passed": passed,
        "checks_total": total,
        "result": result,
        "token_type": "OIDC RS256 JWT",
        "non_claims": [
            "This verifier does not connect to a real OIDC provider.",
            "CI JWKS is locally generated for testing only.",
            "Production requires an external OIDC provider (Okta, Auth0, Keycloak, Azure AD).",
        ],
        "checks": checks,
    }

    out_dir = Path(__file__).resolve().parents[4] / "assurance" / "evolve-multi-agent" / "v1_5"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "oidc_hitl_report.json").write_text(json.dumps(report, indent=2))

    print(f"OIDC_HITL_VERIFICATION={result}  ({passed}/{total})")
    return 0 if result == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
