#!/usr/bin/env python3
"""
verify_materiality_paths.py — v1.9.0 governance path coverage check.

Checks:
  C-01  materiality_score field present in StartRequest (default 78.0)
  C-02  materiality > 85 → FAIL_CLOSED path → status completed_fail_closed
  C-03  70 < materiality ≤ 85 → SCOPE_LIMITED path → status awaiting_human_approval
  C-04  materiality ≤ 70 → PASS path → status completed
  C-05  FAIL_CLOSED receipt has outcome=FAIL_CLOSED
  C-06  SCOPE_LIMITED receipt has outcome=SCOPE_LIMITED
  C-07  PASS receipt has outcome=PASS
  C-08  materiality_score=101 → 422 validation error
  C-09  materiality_score=-1 → 422 validation error
  C-10  /health shows materiality_parametrized=True and all 3 governance_paths

Expected output: MATERIALITY_PATHS_VERIFICATION=PASS (10/10)
"""
from __future__ import annotations

import json
import os
import sys
import uuid
from pathlib import Path

_DEMO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_DEMO_ROOT) not in sys.path:
    sys.path.insert(0, str(_DEMO_ROOT))

os.environ.setdefault("AEM_LOG_LEVEL", "WARNING")

from fastapi.testclient import TestClient  # noqa: E402
import main as _main  # noqa: E402

_INITIATOR_KEY = "demo-initiator-key-001"
_OBSERVER_KEY  = "demo-observer-key-001"


def _tid() -> str:
    return f"mp-{uuid.uuid4().hex[:12]}"


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

    # C-01 materiality_score field in schema
    from main import StartRequest
    import inspect
    fields = StartRequest.model_fields
    has_field = "materiality_score" in fields
    default = fields["materiality_score"].default if has_field else None
    record("C-01-materiality-score-field", has_field and default == 78.0,
           f"default={default}")

    with TestClient(_main.app, raise_server_exceptions=True) as client:
        # C-02 FAIL_CLOSED path (materiality=90)
        tid_fc = _tid()
        r = client.post("/start", json={"thread_id": tid_fc, "materiality_score": 90.0},
                        headers={"X-API-Key": _INITIATOR_KEY})
        status_fc = r.json().get("status", "") if r.status_code == 200 else ""
        record("C-02-fail-closed-path", status_fc == "completed_fail_closed",
               f"status={status_fc!r}")

        # C-03 SCOPE_LIMITED path (materiality=78)
        tid_sl = _tid()
        r = client.post("/start", json={"thread_id": tid_sl, "materiality_score": 78.0},
                        headers={"X-API-Key": _INITIATOR_KEY})
        status_sl = r.json().get("status", "") if r.status_code == 200 else ""
        record("C-03-scope-limited-path", status_sl == "awaiting_human_approval",
               f"status={status_sl!r}")

        # C-04 PASS path (materiality=50)
        tid_pass = _tid()
        r = client.post("/start", json={"thread_id": tid_pass, "materiality_score": 50.0},
                        headers={"X-API-Key": _INITIATOR_KEY})
        status_pass = r.json().get("status", "") if r.status_code == 200 else ""
        record("C-04-pass-path", status_pass == "completed",
               f"status={status_pass!r}")

        # C-05 FAIL_CLOSED receipt outcome
        r = client.get(f"/receipt/{tid_fc}", headers={"X-API-Key": _OBSERVER_KEY})
        outcome_fc = r.json().get("receipt_payload", {}).get("outcome", "") if r.status_code == 200 else ""
        record("C-05-fail-closed-receipt-outcome", outcome_fc == "FAIL_CLOSED",
               f"outcome={outcome_fc!r}")

        # C-06 SCOPE_LIMITED receipt outcome
        r = client.get(f"/receipt/{tid_sl}", headers={"X-API-Key": _OBSERVER_KEY})
        outcome_sl = r.json().get("receipt_payload", {}).get("outcome", "") if r.status_code == 200 else ""
        record("C-06-scope-limited-receipt-outcome", outcome_sl == "SCOPE_LIMITED",
               f"outcome={outcome_sl!r}")

        # C-07 PASS receipt outcome
        r = client.get(f"/receipt/{tid_pass}", headers={"X-API-Key": _OBSERVER_KEY})
        outcome_pass = r.json().get("receipt_payload", {}).get("outcome", "") if r.status_code == 200 else ""
        record("C-07-pass-receipt-outcome", outcome_pass == "PASS",
               f"outcome={outcome_pass!r}")

        # C-08 materiality=101 → 422
        r = client.post("/start", json={"thread_id": _tid(), "materiality_score": 101.0},
                        headers={"X-API-Key": _INITIATOR_KEY})
        record("C-08-above-100-rejected", r.status_code == 422,
               f"status={r.status_code}")

        # C-09 materiality=-1 → 422
        r = client.post("/start", json={"thread_id": _tid(), "materiality_score": -1.0},
                        headers={"X-API-Key": _INITIATOR_KEY})
        record("C-09-below-0-rejected", r.status_code == 422,
               f"status={r.status_code}")

        # C-10 /health fields
        health = client.get("/health").json()
        mat_param = health.get("materiality_parametrized", False)
        gov_paths = health.get("governance_paths", [])
        all_paths = all(p in gov_paths for p in ("FAIL_CLOSED", "SCOPE_LIMITED", "PASS"))
        record("C-10-health-materiality-fields",
               mat_param is True and all_paths,
               f"parametrized={mat_param} paths={gov_paths}")

    return passed, len(checks), checks


def main() -> int:
    print("Materiality Paths Verification — AEM-EVOLVE™ v1.9.0")
    print("=" * 54)
    passed, total, checks = run_checks()
    print()

    result = "PASS" if passed == total else "FAIL"
    report = {
        "component": "verify_materiality_paths",
        "version": "v1.9",
        "checks_passed": passed,
        "checks_total": total,
        "result": result,
        "non_claims": [
            "Materiality score is set by the initiator — not externally audited.",
            "Governance paths are deterministic based on hardcoded thresholds.",
            "This verifier does not test concurrent approval flows.",
        ],
        "checks": checks,
    }

    out_dir = Path(__file__).resolve().parents[4] / "assurance" / "evolve-multi-agent" / "v1_9"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "materiality_paths_report.json").write_text(json.dumps(report, indent=2))

    print(f"MATERIALITY_PATHS_VERIFICATION={result}  ({passed}/{total})")
    return 0 if result == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
