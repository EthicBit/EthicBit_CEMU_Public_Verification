#!/usr/bin/env python3
"""
mlkem768_setup_check.py — validates mlkem library installation and API.

Checks:
  C-01  mlkem package importable
  C-02  ML_KEM class importable from mlkem.ml_kem
  C-03  ML_KEM_768 parameter set importable from mlkem.parameter_set
  C-04  ML_KEM(ML_KEM_768) instantiable
  C-05  key_gen() returns (ek, dk) with correct sizes (ek=1184, dk=2400)
  C-06  encaps(ek) returns (ss, ct) — shared_secret first, ciphertext second
  C-07  decaps(dk, ct) returns shared_secret matching encaps output
  C-08  round-trip: encaps_ss == decaps_ss
  C-09  mode reported is "mlkem" (not simulation)

Expected output: MLKEM768_LIBRARY_STATUS=PASS  mode=mlkem
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent


def run_checks() -> tuple[int, int, list[dict], str]:
    checks: list[dict] = []
    passed = 0
    mode_detected = "unknown"

    def record(name: str, ok: bool, detail: str = "") -> None:
        nonlocal passed
        status = "PASS" if ok else "FAIL"
        checks.append({"check": name, "status": status, "detail": detail})
        if ok:
            passed += 1
        print(f"  {status}  {name}" + (f"  — {detail}" if detail else ""))

    # C-01
    try:
        import mlkem  # type: ignore[import]
        version = getattr(mlkem, "__version__", "unknown")
        record("C-01-mlkem-importable", True, f"version={version}")
    except ImportError as exc:
        record("C-01-mlkem-importable", False, str(exc))
        # Without the library the rest cannot run
        for n in ["C-02", "C-03", "C-04", "C-05", "C-06", "C-07", "C-08", "C-09"]:
            record(f"{n}-skipped", False, "mlkem not installed")
        return passed, len(checks), checks, "simulation"

    # C-02
    try:
        from mlkem.ml_kem import ML_KEM  # type: ignore[import]
        record("C-02-ML_KEM-importable", True)
    except ImportError as exc:
        record("C-02-ML_KEM-importable", False, str(exc))
        ML_KEM = None  # type: ignore[assignment]

    # C-03
    try:
        from mlkem.parameter_set import ML_KEM_768  # type: ignore[import]
        record("C-03-ML_KEM_768-importable", True)
    except ImportError as exc:
        record("C-03-ML_KEM_768-importable", False, str(exc))
        ML_KEM_768 = None  # type: ignore[assignment]

    if ML_KEM is None or ML_KEM_768 is None:
        for n in ["C-04", "C-05", "C-06", "C-07", "C-08", "C-09"]:
            record(f"{n}-skipped", False, "imports failed")
        return passed, len(checks), checks, "simulation"

    # C-04
    try:
        kem = ML_KEM(ML_KEM_768)
        record("C-04-instantiation", True)
    except Exception as exc:
        record("C-04-instantiation", False, str(exc))
        return passed, len(checks), checks, "simulation"

    # C-05
    try:
        ek, dk = kem.key_gen()
        ok = len(ek) == 1184 and len(dk) == 2400
        record("C-05-key-gen-sizes", ok, f"ek={len(ek)}  dk={len(dk)}")
    except Exception as exc:
        record("C-05-key-gen-sizes", False, str(exc))
        return passed, len(checks), checks, "simulation"

    # C-06
    try:
        result = kem.encaps(ek)
        ss, ct = result
        record("C-06-encaps-returns-ss-ct", len(ss) == 32 and len(ct) == 1088,
               f"ss={len(ss)}  ct={len(ct)}")
    except Exception as exc:
        record("C-06-encaps-returns-ss-ct", False, str(exc))
        ss, ct = b"", b""

    # C-07
    try:
        ss2 = kem.decaps(dk, ct)
        record("C-07-decaps-runs", len(ss2) == 32, f"ss2_len={len(ss2)}")
    except Exception as exc:
        record("C-07-decaps-runs", False, str(exc))
        ss2 = b""

    # C-08
    record("C-08-round-trip", ss == ss2 and len(ss) == 32, f"match={ss == ss2}")

    # C-09 mode
    sys.path.insert(0, str(_HERE))
    from mlkem768_wrapper import detect_mode  # type: ignore[import]
    mode_detected = detect_mode()
    record("C-09-mode-is-mlkem", mode_detected == "mlkem", f"mode={mode_detected}")

    return passed, len(checks), checks, mode_detected


def main() -> int:
    print("ML-KEM768 Library Setup Check")
    print("=" * 44)
    passed, total, checks, mode = run_checks()
    print()

    result = "PASS" if passed == total else "FAIL"
    report = {
        "component": "mlkem768_library",
        "version": "v1.4",
        "mode": mode,
        "checks_passed": passed,
        "checks_total": total,
        "result": result,
        "non_claims": [
            "ML-KEM768 is not independently audited.",
            "This wrapper is not a certified cryptographic implementation.",
        ],
        "checks": checks,
    }

    out_dir = _HERE.parent.parent.parent.parent / "assurance" / "evolve-multi-agent" / "v1_4"
    out_dir.mkdir(parents=True, exist_ok=True)
    report_path = out_dir / "mlkem768_library_report.json"
    report_path.write_text(json.dumps(report, indent=2))

    print(f"MLKEM768_LIBRARY_STATUS={result}  mode={mode}")
    return 0 if result == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
