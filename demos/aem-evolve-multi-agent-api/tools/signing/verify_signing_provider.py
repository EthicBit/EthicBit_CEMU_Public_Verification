#!/usr/bin/env python3
"""
verify_signing_provider.py — round-trip verifier for SigningProvider abstraction.

Checks:
  C-01  SigningProvider ABC has required abstract methods
  C-02  EnvSigningProvider raises EnvironmentError when env var not set
  C-03  FileSigningProvider raises FileNotFoundError for missing file
  C-04  FileSigningProvider loads key and produces valid public_key_pem
  C-05  round-trip sign / verify returns True for correct message
  C-06  verify returns False for tampered message
  C-07  verify returns False for tampered signature
  C-08  public_key_pem is valid PEM (starts with -----BEGIN)

Expected output: SIGNING_PROVIDER_VERIFICATION=PASS
"""

from __future__ import annotations

import inspect
import json
import os
import sys
import tempfile
from pathlib import Path

# ---------------------------------------------------------------------------
# Path bootstrap
# ---------------------------------------------------------------------------
_HERE = Path(__file__).resolve().parent
_TOOLS = _HERE.parent
sys.path.insert(0, str(_TOOLS))

from signing.signing_provider import SigningProvider  # noqa: E402
from signing.env_signing_provider import EnvSigningProvider  # noqa: E402
from signing.file_signing_provider import FileSigningProvider  # noqa: E402


def _generate_test_key_pem() -> bytes:
    """Generate a fresh Ed25519 private key and return PEM bytes."""
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
    from cryptography.hazmat.primitives import serialization

    key = Ed25519PrivateKey.generate()
    return key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )


def run_checks() -> tuple[int, int, list[dict]]:
    checks = []
    passed = 0

    def record(name: str, ok: bool, detail: str = "") -> None:
        nonlocal passed
        status = "PASS" if ok else "FAIL"
        checks.append({"check": name, "status": status, "detail": detail})
        if ok:
            passed += 1
        print(f"  {status}  {name}" + (f"  — {detail}" if detail else ""))

    # C-01 ABC abstract methods
    abstract = {
        name
        for name, m in inspect.getmembers(SigningProvider, predicate=inspect.isfunction)
        if getattr(m, "__isabstractmethod__", False)
    }
    record("C-01-ABC-abstract-methods", abstract == {"sign", "verify", "public_key_pem"},
           f"abstract={sorted(abstract)}")

    # C-02 EnvSigningProvider raises when var not set
    old_val = os.environ.pop("ETHICBIT_ED25519_PRIVATE_KEY_PEM", None)
    try:
        try:
            EnvSigningProvider()
            record("C-02-EnvProvider-missing-var", False, "no exception raised")
        except EnvironmentError as exc:
            record("C-02-EnvProvider-missing-var", True, str(exc)[:60])
    finally:
        if old_val is not None:
            os.environ["ETHICBIT_ED25519_PRIVATE_KEY_PEM"] = old_val

    # Generate a test key for remaining checks
    key_pem = _generate_test_key_pem()

    # C-03 FileSigningProvider raises for missing file
    try:
        FileSigningProvider("/nonexistent/path/key.pem")
        record("C-03-FileProvider-missing-file", False, "no exception raised")
    except FileNotFoundError as exc:
        record("C-03-FileProvider-missing-file", True, str(exc)[:60])

    # Write key to temp file for remaining tests
    with tempfile.NamedTemporaryFile(suffix=".pem", delete=False) as f:
        f.write(key_pem)
        tmp_path = f.name

    try:
        provider = FileSigningProvider(tmp_path)

        # C-04 public_key_pem returns valid PEM
        pub_pem = provider.public_key_pem()
        record("C-04-FileProvider-public-key-pem",
               isinstance(pub_pem, bytes) and pub_pem.startswith(b"-----BEGIN"),
               f"length={len(pub_pem)}")

        message = b"AEM-EVOLVE v1.4 signing provider round-trip test"

        # C-05 round-trip sign/verify
        sig = provider.sign(message)
        ok = provider.verify(message, sig)
        record("C-05-roundtrip-sign-verify", ok, f"sig_length={len(sig)}")

        # C-06 verify returns False for tampered message
        tampered_msg = b"tampered: " + message
        ok = not provider.verify(tampered_msg, sig)
        record("C-06-tampered-message-rejected", ok)

        # C-07 verify returns False for tampered signature
        tampered_sig = bytes([sig[0] ^ 0xFF]) + sig[1:]
        ok = not provider.verify(message, tampered_sig)
        record("C-07-tampered-signature-rejected", ok)

        # C-08 public_key_pem starts with -----BEGIN
        ok = pub_pem.startswith(b"-----BEGIN")
        record("C-08-public-key-pem-format", ok, pub_pem[:27].decode())

    finally:
        Path(tmp_path).unlink(missing_ok=True)

    return passed, len(checks), checks


def main() -> int:
    print("SigningProvider Verification")
    print("=" * 44)
    passed, total, checks = run_checks()
    print()

    result = "PASS" if passed == total else "FAIL"
    summary = {
        "component": "signing_provider",
        "version": "v1.4",
        "checks_passed": passed,
        "checks_total": total,
        "result": result,
        "non_claims": [
            "SigningProvider is not HSM-backed.",
            "HSM integration requires an external implementation of this ABC.",
        ],
        "checks": checks,
    }

    out_dir = _HERE.parent.parent.parent.parent / "assurance" / "evolve-multi-agent" / "v1_4"
    out_dir.mkdir(parents=True, exist_ok=True)
    report_path = out_dir / "signing_provider_report.json"
    report_path.write_text(json.dumps(summary, indent=2))

    print(f"SIGNING_PROVIDER_VERIFICATION={result}  ({passed}/{total})")
    print(f"report → {report_path.relative_to(Path.cwd()) if report_path.is_relative_to(Path.cwd()) else report_path}")
    return 0 if result == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
