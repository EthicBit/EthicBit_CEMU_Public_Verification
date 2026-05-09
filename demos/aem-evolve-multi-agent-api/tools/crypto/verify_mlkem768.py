#!/usr/bin/env python3
"""ML-KEM768 round-trip verification — AEM-EVOLVE™ v1.3.

Verifies:
  1. Key generation produces keys of correct size
  2. Encapsulation produces ciphertext + shared secret of correct size
  3. Decapsulation recovers the same shared secret (round-trip integrity)
  4. Two independent encapsulations produce different ciphertexts (randomness)
  5. Shared secrets from different key pairs do not match (isolation)

Output: MLKEM768_STATUS=PASS | FAIL
"""
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]
V1_3      = REPO_ROOT / "assurance/evolve-multi-agent/v1_3"
REPORT_OUT = V1_3 / "mlkem768_kem_report.json"

import importlib.util, os
sys.path.insert(0, str(Path(__file__).parent))
from mlkem768_wrapper import keygen, encapsulate, decapsulate, detect_mode

# Expected sizes for ML-KEM768 (FIPS 203)
EXPECTED = {
    "mlkem":      {"pk": 1184, "sk": 2400, "ct": 1088, "ss": 32},
    "kyber_py":   {"pk": 1184, "sk": 2400, "ct": 1088, "ss": 32},
    "simulation": {"pk": 1184, "sk": 2400, "ct": 1088, "ss": 32},
}


def _pass(checks, cid, detail="ok"):
    checks.append({"check_id": cid, "status": "PASS", "detail": detail})


def _fail(checks, cid, detail):
    checks.append({"check_id": cid, "status": "FAIL", "detail": detail})


def main() -> int:
    mode = detect_mode()
    print(f"[ML-KEM768 VERIFIER] mode={mode}")

    checks = []
    sizes  = EXPECTED[mode]

    # C-01: keygen sizes
    kp = keygen()
    if len(kp.public_key) == sizes["pk"] and len(kp.secret_key) == sizes["sk"]:
        _pass(checks, "C-01-KEYGEN-SIZES",
              f"pk={len(kp.public_key)}B sk={len(kp.secret_key)}B")
    else:
        _fail(checks, "C-01-KEYGEN-SIZES",
              f"pk={len(kp.public_key)} expected {sizes['pk']}; sk={len(kp.secret_key)} expected {sizes['sk']}")

    # C-02: encapsulate sizes
    enc = encapsulate(kp.public_key)
    if len(enc.ciphertext) == sizes["ct"] and len(enc.shared_secret) == sizes["ss"]:
        _pass(checks, "C-02-ENC-SIZES",
              f"ct={len(enc.ciphertext)}B ss={len(enc.shared_secret)}B")
    else:
        _fail(checks, "C-02-ENC-SIZES",
              f"ct={len(enc.ciphertext)} expected {sizes['ct']}; ss={len(enc.shared_secret)} expected {sizes['ss']}")

    # C-03: round-trip — decapsulate recovers shared secret
    recovered = decapsulate(kp.secret_key, enc.ciphertext)
    if recovered == enc.shared_secret:
        _pass(checks, "C-03-ROUND-TRIP", "decapsulate(sk, ct) == enc.shared_secret")
    else:
        _fail(checks, "C-03-ROUND-TRIP", "shared secret mismatch after decapsulation")

    # C-04: randomness — two encapsulations differ
    enc2 = encapsulate(kp.public_key)
    if enc.ciphertext != enc2.ciphertext:
        _pass(checks, "C-04-RANDOMNESS", "two encapsulations produce different ciphertexts")
    else:
        # In simulation mode with no nonce this would fail — but we added nonce
        _fail(checks, "C-04-RANDOMNESS", "encapsulations are identical — randomness failure")

    # C-05: key isolation — different key pair, different shared secret
    kp2   = keygen()
    enc3  = encapsulate(kp2.public_key)
    dec_wrong = decapsulate(kp.secret_key, enc3.ciphertext)
    if dec_wrong != enc3.shared_secret:
        _pass(checks, "C-05-ISOLATION", "different key pairs produce independent shared secrets")
    else:
        _fail(checks, "C-05-ISOLATION", "key isolation failure — shared secrets collide across key pairs")

    failed  = [c for c in checks if c["status"] == "FAIL"]
    overall = "PASS" if not failed else "FAIL"

    report = {
        "schema_id":   "AEM_EVOLVE_MLKEM768_KEM_REPORT_V1_3",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "mode":        mode,
        "verification_result": overall,
        "checks_passed": len([c for c in checks if c["status"] == "PASS"]),
        "checks_failed": len(failed),
        "checks":      checks,
        "expected_sizes": sizes,
        "non_claims": [
            "This wrapper is not a certified cryptographic implementation.",
            "This wrapper does not replace Ed25519/ML-DSA signing.",
            "Simulation mode is NOT cryptographically secure.",
            "This wrapper has not been independently audited.",
        ],
    }

    V1_3.mkdir(parents=True, exist_ok=True)
    with open(REPORT_OUT, "w") as f:
        json.dump(report, f, indent=2)

    for c in checks:
        mark = "✓" if c["status"] == "PASS" else "✗"
        print(f"  {mark} [{c['check_id']}] {c['detail']}")

    print(f"MLKEM768_STATUS={overall}")
    return 0 if overall == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
