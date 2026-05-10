#!/usr/bin/env python3
"""
verify_key_persistence.py — v1.7.0 signing key persistence check.

Checks:
  C-01  FileSigningProvider is importable
  C-02  _init_signing_provider is importable
  C-03  signing_key.pem exists in DEMO_ROOT after server initializes
  C-04  signing_key.pem is a valid PEM-encoded Ed25519 private key
  C-05  _SIGNING_STATUS is SIGNED_Ed25519_FILE or SIGNED_Ed25519_ENV (not ephemeral)
  C-06  FileSigningProvider.sign produces 64-byte signature
  C-07  FileSigningProvider.verify round-trip passes
  C-08  FileSigningProvider loaded from same file produces same public key
  C-09  GET /health key_persistence field is present
  C-10  Signing key from DEMO_ROOT matches public key in /health (via algorithm match)

Expected output: KEY_PERSISTENCE_VERIFICATION=PASS (10/10)
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

import main as _main  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402


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

    # C-01 FileSigningProvider importable
    try:
        from signing.file_signing_provider import FileSigningProvider
        record("C-01-file-signing-provider-importable", True)
    except Exception as exc:
        record("C-01-file-signing-provider-importable", False, str(exc))
        FileSigningProvider = None  # type: ignore[assignment]

    # C-02 _init_signing_provider importable
    try:
        assert callable(_main._init_signing_provider)
        record("C-02-init-signing-provider-importable", True)
    except Exception as exc:
        record("C-02-init-signing-provider-importable", False, str(exc))

    # C-03 signing_key.pem exists
    key_file = _DEMO_ROOT / "signing_key.pem"
    record("C-03-signing-key-pem-exists", key_file.exists(),
           f"path={key_file}")

    # C-04 PEM is valid Ed25519 private key
    pem_valid = False
    if key_file.exists():
        try:
            from cryptography.hazmat.primitives import serialization
            pem = key_file.read_bytes()
            key = serialization.load_pem_private_key(pem, password=None)
            from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
            pem_valid = isinstance(key, Ed25519PrivateKey)
        except Exception as exc:
            pem_valid = False
    record("C-04-pem-is-valid-ed25519", pem_valid)

    # C-05 SIGNING_STATUS is FILE or ENV (not ephemeral)
    status = _main._SIGNING_STATUS
    is_persistent = "FILE" in status or "ENV" in status
    record("C-05-signing-status-not-ephemeral", is_persistent,
           f"status={status!r}")

    # C-06 FileSigningProvider.sign produces 64 bytes
    if FileSigningProvider and key_file.exists():
        try:
            from signing.file_signing_provider import FileSigningProvider as FSP
            fsp = FSP(key_file)
            sig = fsp.sign(b"test-message")
            record("C-06-file-provider-sign-64-bytes", len(sig) == 64,
                   f"len={len(sig)}")
        except Exception as exc:
            record("C-06-file-provider-sign-64-bytes", False, str(exc))
    else:
        record("C-06-file-provider-sign-64-bytes", False, "FileSigningProvider or key_file unavailable")

    # C-07 verify round-trip
    if FileSigningProvider and key_file.exists():
        try:
            from signing.file_signing_provider import FileSigningProvider as FSP
            fsp = FSP(key_file)
            msg = b"round-trip-test"
            sig = fsp.sign(msg)
            ok = fsp.verify(msg, sig)
            record("C-07-verify-roundtrip", ok, f"ok={ok}")
        except Exception as exc:
            record("C-07-verify-roundtrip", False, str(exc))
    else:
        record("C-07-verify-roundtrip", False, "FileSigningProvider or key_file unavailable")

    # C-08 two loads from same file → same public key
    if FileSigningProvider and key_file.exists():
        try:
            from signing.file_signing_provider import FileSigningProvider as FSP
            fsp1 = FSP(key_file)
            fsp2 = FSP(key_file)
            same = fsp1.public_key_pem() == fsp2.public_key_pem()
            record("C-08-same-file-same-public-key", same)
        except Exception as exc:
            record("C-08-same-file-same-public-key", False, str(exc))
    else:
        record("C-08-same-file-same-public-key", False, "FileSigningProvider or key_file unavailable")

    # C-09 / C-10 — via TestClient
    with TestClient(_main.app, raise_server_exceptions=True) as client:
        r = client.get("/health")
        health = r.json() if r.status_code == 200 else {}

        # C-09 key_persistence field present
        kp = health.get("key_persistence", "")
        record("C-09-health-key-persistence-field", bool(kp), f"field={kp!r}")

        # C-10 algorithm in /health matches provider algorithm
        algo = health.get("signing_provider", "")
        expected_algo = _main._signing_provider.algorithm()
        record("C-10-health-algo-matches-provider", algo == expected_algo,
               f"health={algo!r} provider={expected_algo!r}")

    return passed, len(checks), checks


def main() -> int:
    print("Key Persistence Verification — AEM-EVOLVE™ v1.7.0")
    print("=" * 52)
    passed, total, checks = run_checks()
    print()

    result = "PASS" if passed == total else "FAIL"
    report = {
        "component": "verify_key_persistence",
        "version": "v1.7",
        "checks_passed": passed,
        "checks_total": total,
        "result": result,
        "non_claims": [
            "File-based key is not HSM-backed.",
            "Key stored unencrypted on disk — not enterprise key custody.",
            "File key persists across restarts but is not rotated automatically.",
        ],
        "checks": checks,
    }

    out_dir = Path(__file__).resolve().parents[4] / "assurance" / "evolve-multi-agent" / "v1_7"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "key_persistence_report.json").write_text(json.dumps(report, indent=2))

    print(f"KEY_PERSISTENCE_VERIFICATION={result}  ({passed}/{total})")
    return 0 if result == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
