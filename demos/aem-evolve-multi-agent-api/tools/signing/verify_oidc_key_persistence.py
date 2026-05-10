#!/usr/bin/env python3
"""
verify_oidc_key_persistence.py — v1.9.0 OIDC key file persistence check.

Checks:
  C-01  oidc_key.pem exists after server init
  C-02  File contains a valid RSA private key
  C-03  Key size is 2048 bits
  C-04  load_or_generate returns deterministic kid on repeated calls
  C-05  kid matches _main._oidc_key_pair.key_id (stable across import)
  C-06  Sign JWT with loaded key, verify against its JWKS → True
  C-07  Reload key independently, verify JWT signed before reload → True
  C-08  /oidc/jwks kid matches key_id from load_or_generate
  C-09  /health shows oidc_key_persistence=FILE_BASED
  C-10  key_id is not random (two loads return same kid)

Expected output: OIDC_KEY_PERSISTENCE_VERIFICATION=PASS (10/10)
"""
from __future__ import annotations

import json
import os
import sys
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
from main import DEMO_ROOT, _OIDC_KEY_FILE_NAME  # noqa: E402

_OIDC_KEY_FILE = DEMO_ROOT / _OIDC_KEY_FILE_NAME


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

    # C-01 oidc_key.pem exists
    record("C-01-oidc-key-pem-exists", _OIDC_KEY_FILE.exists(),
           f"path={_OIDC_KEY_FILE}")

    # C-02 Valid RSA PEM
    try:
        from cryptography.hazmat.primitives import serialization
        from cryptography.hazmat.primitives.asymmetric.rsa import RSAPrivateKey
        pem = _OIDC_KEY_FILE.read_bytes()
        key = serialization.load_pem_private_key(pem, password=None)
        record("C-02-valid-rsa-pem", isinstance(key, RSAPrivateKey))
    except Exception as exc:
        record("C-02-valid-rsa-pem", False, str(exc)[:80])
        key = None

    # C-03 Key size 2048
    if key is not None:
        record("C-03-key-size-2048", key.key_size == 2048, f"size={key.key_size}")
    else:
        record("C-03-key-size-2048", False, "key not loaded")

    # C-04 Deterministic kid on repeated calls
    from hitl.oidc_token_generator import OidcTestKeyPair
    kp1 = OidcTestKeyPair.load_or_generate(_OIDC_KEY_FILE)
    kp2 = OidcTestKeyPair.load_or_generate(_OIDC_KEY_FILE)
    record("C-04-deterministic-kid", kp1.key_id == kp2.key_id,
           f"kid1={kp1.key_id!r} kid2={kp2.key_id!r}")

    # C-05 kid matches _main._oidc_key_pair
    main_kid = getattr(_main._oidc_key_pair, "key_id", None)
    record("C-05-kid-matches-main", kp1.key_id == main_kid,
           f"file={kp1.key_id!r} main={main_kid!r}")

    # C-06 Sign JWT, verify against JWKS
    from hitl.oidc_token_generator import generate_token
    from hitl.oidc_hitl_identity_verifier import verify_oidc_token
    policy = _main._OIDC_POLICY
    try:
        token = generate_token(kp1, sub="approver-001", event_id="test-persist",
                               issuer=policy["issuer"], audience=policy["audience"])
        ok, reason, _ = verify_oidc_token(token, kp1.jwks(), policy)
        record("C-06-sign-verify-roundtrip", ok, reason)
    except Exception as exc:
        record("C-06-sign-verify-roundtrip", False, str(exc)[:80])
        token = None

    # C-07 Cross-reload: token signed by kp1 verifies against kp2 JWKS
    if token:
        try:
            ok, reason, _ = verify_oidc_token(token, kp2.jwks(), policy)
            record("C-07-cross-reload-verify", ok, reason)
        except Exception as exc:
            record("C-07-cross-reload-verify", False, str(exc)[:80])
    else:
        record("C-07-cross-reload-verify", False, "no token from C-06")

    with TestClient(_main.app, raise_server_exceptions=True) as client:
        # C-08 /oidc/jwks kid matches load_or_generate
        r = client.get("/oidc/jwks")
        jwks = r.json() if r.status_code == 200 else {}
        keys = jwks.get("keys", [])
        jwks_kid = keys[0]["kid"] if keys else ""
        record("C-08-jwks-kid-matches-file", jwks_kid == kp1.key_id,
               f"jwks={jwks_kid!r} file={kp1.key_id!r}")

        # C-09 /health shows FILE_BASED
        health = client.get("/health").json()
        oidc_persist = health.get("oidc_key_persistence", "")
        record("C-09-health-oidc-key-persistence", oidc_persist == "FILE_BASED",
               f"field={oidc_persist!r}")

    # C-10 kid is not random (same as C-04 but explicit label)
    kp3 = OidcTestKeyPair.load_or_generate(_OIDC_KEY_FILE)
    record("C-10-kid-not-random", kp1.key_id == kp3.key_id,
           f"stable={kp1.key_id == kp3.key_id}")

    return passed, len(checks), checks


def main() -> int:
    print("OIDC Key Persistence Verification — AEM-EVOLVE™ v1.9.0")
    print("=" * 56)
    passed, total, checks = run_checks()
    print()

    result = "PASS" if passed == total else "FAIL"
    report = {
        "component": "verify_oidc_key_persistence",
        "version": "v1.9",
        "checks_passed": passed,
        "checks_total": total,
        "result": result,
        "non_claims": [
            "OIDC key file is not HSM-backed.",
            "Key stored unencrypted on disk — not enterprise key management.",
            "Production requires external OIDC provider with managed key custody.",
        ],
        "checks": checks,
    }

    out_dir = Path(__file__).resolve().parents[4] / "assurance" / "evolve-multi-agent" / "v1_9"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "oidc_key_persistence_report.json").write_text(json.dumps(report, indent=2))

    print(f"OIDC_KEY_PERSISTENCE_VERIFICATION={result}  ({passed}/{total})")
    return 0 if result == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
