#!/usr/bin/env python3
"""
verify_hsm_signing_providers.py — ABC compliance + graceful-fallback verifier
for Pkcs11SigningProvider and KmsSigningProvider.

Checks:
  C-01  Pkcs11SigningProvider is importable (class exists)
  C-02  Pkcs11SigningProvider inherits from SigningProvider ABC
  C-03  Pkcs11SigningProvider raises ImportError when pkcs11 not installed
  C-04  ImportError message contains install guidance for pkcs11
  C-05  KmsSigningProvider is importable (class exists)
  C-06  KmsSigningProvider inherits from SigningProvider ABC
  C-07  KmsSigningProvider raises ImportError when boto3 not installed
  C-08  ImportError message contains install guidance for boto3
  C-09  FileSigningProvider (software) substitutes as drop-in for HSM slot
  C-10  algorithm() returns non-empty string on software fallback

Expected output: HSM_SIGNING_VERIFICATION=PASS
"""

from __future__ import annotations

import inspect
import json
import sys
import tempfile
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_TOOLS = _HERE.parent
sys.path.insert(0, str(_TOOLS))

from signing.signing_provider import SigningProvider  # noqa: E402
from signing.pkcs11_signing_provider import Pkcs11SigningProvider  # noqa: E402
from signing.kms_signing_provider import KmsSigningProvider  # noqa: E402
from signing.file_signing_provider import FileSigningProvider  # noqa: E402


def _generate_key_pem() -> bytes:
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
    from cryptography.hazmat.primitives import serialization
    key = Ed25519PrivateKey.generate()
    return key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )


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

    # C-01 PKCS#11 class importable
    record("C-01-pkcs11-class-importable", issubclass(Pkcs11SigningProvider, object))

    # C-02 inherits SigningProvider
    record("C-02-pkcs11-inherits-abc", issubclass(Pkcs11SigningProvider, SigningProvider))

    # C-03 raises ImportError when pkcs11 not installed (simulate)
    _orig = sys.modules.get("pkcs11")
    sys.modules["pkcs11"] = None  # type: ignore[assignment]
    try:
        Pkcs11SigningProvider()
        record("C-03-pkcs11-import-error", False, "no exception raised")
        err_msg = ""
    except ImportError as exc:
        err_msg = str(exc)
        record("C-03-pkcs11-import-error", True, err_msg[:60])
    except Exception as exc:
        record("C-03-pkcs11-import-error", False, str(exc)[:60])
        err_msg = ""
    finally:
        if _orig is None:
            sys.modules.pop("pkcs11", None)
        else:
            sys.modules["pkcs11"] = _orig

    # C-04 ImportError has guidance
    record("C-04-pkcs11-error-guidance",
           "pkcs11" in err_msg.lower() and "pip install" in err_msg.lower(),
           err_msg[:80])

    # C-05 KMS class importable
    record("C-05-kms-class-importable", issubclass(KmsSigningProvider, object))

    # C-06 inherits SigningProvider
    record("C-06-kms-inherits-abc", issubclass(KmsSigningProvider, SigningProvider))

    # C-07 raises ImportError when boto3 not installed
    _orig_boto = sys.modules.get("boto3")
    sys.modules["boto3"] = None  # type: ignore[assignment]
    try:
        KmsSigningProvider()
        record("C-07-kms-import-error", False, "no exception raised")
        kms_err = ""
    except ImportError as exc:
        kms_err = str(exc)
        record("C-07-kms-import-error", True, kms_err[:60])
    except Exception as exc:
        record("C-07-kms-import-error", False, str(exc)[:60])
        kms_err = ""
    finally:
        if _orig_boto is None:
            sys.modules.pop("boto3", None)
        else:
            sys.modules["boto3"] = _orig_boto

    # C-08 ImportError has guidance
    record("C-08-kms-error-guidance",
           "boto3" in kms_err.lower() and "pip install" in kms_err.lower(),
           kms_err[:80])

    # C-09 FileSigningProvider substitutes as drop-in for HSM slot
    key_pem = _generate_key_pem()
    with tempfile.NamedTemporaryFile(suffix=".pem", delete=False) as f:
        f.write(key_pem)
        tmp = f.name
    try:
        provider: SigningProvider = FileSigningProvider(tmp)
        msg = b"hsm-signing-provider-drop-in-test"
        sig = provider.sign(msg)
        ok = provider.verify(msg, sig)
        record("C-09-software-fallback-drop-in", ok,
               f"isinstance(SigningProvider)={isinstance(provider, SigningProvider)}")

        # C-10 algorithm() non-empty
        algo = provider.algorithm()
        record("C-10-algorithm-non-empty", bool(algo), f"algorithm={algo!r}")
    finally:
        Path(tmp).unlink(missing_ok=True)

    return passed, len(checks), checks


def main() -> int:
    print("HSM Signing Provider Verification")
    print("=" * 44)
    passed, total, checks = run_checks()
    print()

    result = "PASS" if passed == total else "FAIL"
    report = {
        "component": "hsm_signing_providers",
        "version": "v1.5",
        "checks_passed": passed,
        "checks_total": total,
        "result": result,
        "non_claims": [
            "Pkcs11SigningProvider is not production-tested against real hardware.",
            "KmsSigningProvider is not production-tested against a live AWS KMS key.",
            "SoftHSM is a software HSM suitable for testing only.",
            "Production use requires a FIPS 140-2/3 certified HSM or valid AWS credentials.",
        ],
        "checks": checks,
    }

    out_dir = _HERE.parent.parent.parent.parent / "assurance" / "evolve-multi-agent" / "v1_5"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "hsm_signing_report.json").write_text(json.dumps(report, indent=2))

    print(f"HSM_SIGNING_VERIFICATION={result}  ({passed}/{total})")
    return 0 if result == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
