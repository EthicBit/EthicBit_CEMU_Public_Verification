#!/usr/bin/env python3
"""
validate_async_postgres_adapter.py — contract validator for AsyncPostgresAdapter.

No live database required.  Validates interface shape, import behaviour,
and method signatures by inspection.

Checks:
  C-01  AsyncPostgresAdapter class is defined in db_adapter.py
  C-02  Class has async classmethod `create`
  C-03  Class has async method `execute`
  C-04  Class has async method `fetch`
  C-05  Class has async method `fetchrow`
  C-06  Class has async method `fetchval`
  C-07  Class has async method `ping`
  C-08  Class has async method `close`
  C-09  asyncpg importable (library installed)
  C-10  Missing asyncpg raises ImportError with helpful message

Expected output: ASYNC_POSTGRES_ADAPTER_VALIDATION=PASS
"""

from __future__ import annotations

import asyncio
import inspect
import json
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_ROOT = _HERE.parent.parent
sys.path.insert(0, str(_ROOT))

from db_adapter import AsyncPostgresAdapter  # noqa: E402


def _is_async(obj: object) -> bool:
    return inspect.iscoroutinefunction(obj)


def _is_classmethod_async(cls: type, name: str) -> bool:
    method = getattr(cls, name, None)
    if method is None:
        return False
    return _is_async(method)


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

    # C-01 Class defined
    record("C-01-class-defined", True, f"AsyncPostgresAdapter from db_adapter")

    # C-02 create classmethod async
    create = getattr(AsyncPostgresAdapter, "create", None)
    ok = create is not None and _is_async(create)
    record("C-02-create-async-classmethod", ok)

    # C-03..C-08 instance methods
    for num, method_name in [
        ("C-03", "execute"),
        ("C-04", "fetch"),
        ("C-05", "fetchrow"),
        ("C-06", "fetchval"),
        ("C-07", "ping"),
        ("C-08", "close"),
    ]:
        method = getattr(AsyncPostgresAdapter, method_name, None)
        ok = method is not None and _is_async(method)
        record(f"{num}-{method_name}-async", ok)

    # C-09 asyncpg importable
    try:
        import asyncpg  # type: ignore[import]
        version = getattr(asyncpg, "__version__", "unknown")
        record("C-09-asyncpg-importable", True, f"version={version}")
    except ImportError as exc:
        record("C-09-asyncpg-importable", False, str(exc))

    # C-10 ImportError with message when asyncpg missing (simulate)
    import sys as _sys
    import unittest.mock as mock

    original = _sys.modules.get("asyncpg")
    _sys.modules["asyncpg"] = None  # type: ignore[assignment]

    async def _try_create() -> str:
        try:
            await AsyncPostgresAdapter.create("postgresql://localhost/test")
            return "no-error"
        except ImportError as exc:
            return str(exc)
        except Exception as exc:
            return f"other: {exc}"

    error_msg = asyncio.run(_try_create())
    if original is None:
        _sys.modules.pop("asyncpg", None)
    else:
        _sys.modules["asyncpg"] = original

    ok = "asyncpg" in error_msg.lower() and error_msg != "no-error"
    record("C-10-missing-asyncpg-helpful-error", ok, error_msg[:80])

    return passed, len(checks), checks


def main() -> int:
    print("AsyncPostgresAdapter Contract Validator")
    print("=" * 44)
    passed, total, checks = run_checks()
    print()

    result = "PASS" if passed == total else "FAIL"
    report = {
        "component": "async_postgres_adapter",
        "version": "v1.4",
        "checks_passed": passed,
        "checks_total": total,
        "result": result,
        "non_claims": [
            "AsyncPostgresAdapter is not production-tested at scale.",
            "Does not replace PostgresAdapter for synchronous workloads.",
        ],
        "checks": checks,
    }

    out_dir = _HERE.parent.parent.parent.parent / "assurance" / "evolve-multi-agent" / "v1_4"
    out_dir.mkdir(parents=True, exist_ok=True)
    report_path = out_dir / "async_postgres_adapter_report.json"
    report_path.write_text(json.dumps(report, indent=2))

    print(f"ASYNC_POSTGRES_ADAPTER_VALIDATION={result}  ({passed}/{total})")
    return 0 if result == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
