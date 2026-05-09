#!/usr/bin/env python3
"""
dependency_validator.py — runtime dependency validator for AEM-EVOLVE™.

Classifies packages as REQUIRED or OPTIONAL.
REQUIRED missing  → check FAIL (raises overall result to FAIL).
OPTIONAL missing  → WARN (overall result remains PASS with warnings).

Checks:
  C-01  Python version >= 3.11
  C-02  fastapi (REQUIRED — API server)
  C-03  cryptography (REQUIRED — signing provider, OIDC JWT)
  C-04  mlkem (REQUIRED — ML-KEM768 post-quantum KEM)
  C-05  asyncpg (REQUIRED — async PostgreSQL adapter)
  C-06  langgraph (OPTIONAL — LangGraph state machine)
  C-07  anthropic (OPTIONAL — LLM advisory adapter)
  C-08  psycopg2 (OPTIONAL — sync PostgreSQL adapter)
  C-09  uvicorn (OPTIONAL — ASGI server for production)
  C-10  pytest (OPTIONAL — test suite)

Expected output: DEPENDENCY_VALIDATION=PASS
"""

from __future__ import annotations

import importlib
import json
import sys
from pathlib import Path

PACKAGES = [
    # (check_id, import_name, display_name, tier)
    ("C-02", "fastapi",       "fastapi",       "REQUIRED"),
    ("C-03", "cryptography",  "cryptography",  "REQUIRED"),
    ("C-04", "mlkem",         "mlkem",         "REQUIRED"),
    ("C-05", "asyncpg",       "asyncpg",       "REQUIRED"),
    ("C-06", "langgraph",     "langgraph",     "OPTIONAL"),
    ("C-07", "anthropic",     "anthropic",     "OPTIONAL"),
    ("C-08", "psycopg2",      "psycopg2",      "OPTIONAL"),
    ("C-09", "uvicorn",       "uvicorn",       "OPTIONAL"),
    ("C-10", "pytest",        "pytest",        "OPTIONAL"),
]


def _get_version(module) -> str:
    for attr in ("__version__", "VERSION", "version"):
        v = getattr(module, attr, None)
        if v:
            return str(v)
    return "unknown"


def run_checks() -> tuple[int, int, list[dict]]:
    checks: list[dict] = []
    passed = 0
    warnings: list[str] = []

    def record(name: str, ok: bool, detail: str = "", warn: bool = False) -> None:
        nonlocal passed
        if warn and not ok:
            status = "WARN"
            warnings.append(name)
        else:
            status = "PASS" if ok else "FAIL"
        if ok or warn:
            passed += 1
        checks.append({"check": name, "status": status, "detail": detail})
        print(f"  {status}  {name}" + (f"  — {detail}" if detail else ""))

    # C-01 Python version
    major, minor = sys.version_info[:2]
    ok = (major, minor) >= (3, 11)
    record("C-01-python-version", ok, f"{sys.version.split()[0]}")

    # Packages
    for check_id, import_name, display_name, tier in PACKAGES:
        try:
            mod = importlib.import_module(import_name)
            version = _get_version(mod)
            record(f"{check_id}-{display_name}", True, f"v{version}  [{tier}]")
        except ImportError:
            is_optional = tier == "OPTIONAL"
            record(f"{check_id}-{display_name}", False,
                   f"NOT INSTALLED  [{tier}]  → pip install {display_name}",
                   warn=is_optional)

    return passed, len(checks), checks


def main() -> int:
    print("AEM-EVOLVE™ Runtime Dependency Validator")
    print("=" * 44)
    passed, total, checks = run_checks()
    print()

    # PASS if all REQUIRED checks passed (OPTIONAL misses count as WARN/PASS)
    failed = [c for c in checks if c["status"] == "FAIL"]
    warned = [c for c in checks if c["status"] == "WARN"]
    result = "PASS" if not failed else "FAIL"

    if warned:
        print(f"  WARNINGS ({len(warned)} optional packages missing):")
        for c in warned:
            print(f"    {c['check']}: {c['detail']}")
        print()

    report = {
        "component": "dependency_validator",
        "version": "v1.5",
        "checks_passed": passed,
        "checks_total": total,
        "result": result,
        "failed_required": [c["check"] for c in failed],
        "warned_optional": [c["check"] for c in warned],
        "checks": checks,
    }

    out_dir = Path(__file__).resolve().parents[4] / "assurance" / "evolve-multi-agent" / "v1_5"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "dependency_validation_report.json").write_text(json.dumps(report, indent=2))

    print(f"DEPENDENCY_VALIDATION={result}  ({passed}/{total})")
    if warned:
        print(f"  ({len(warned)} optional packages missing — install for full functionality)")
    return 0 if result == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
