#!/usr/bin/env python3
"""Full-stack independent reproduction verifier — AEM-EVOLVE™ v1.3.

Runs all v1.1 + v1.2 + v1.3 verification scripts end-to-end and emits
a single FULL_STACK_VERIFICATION=PASS | FAIL with per-component results.

Designed for independent reproducers — anyone cloning this repository
can run this script to verify the entire AEM-EVOLVE™ assurance stack.

Output: FULL_STACK_VERIFICATION=PASS | FAIL
"""
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]
V1_3      = REPO_ROOT / "assurance/evolve-multi-agent/v1_3"
REPORT_OUT = V1_3 / "REPRODUCTION_REPORT.json"
TOOLS     = REPO_ROOT / "demos/aem-evolve-multi-agent-api/tools"
ADV_TESTS = REPO_ROOT / "demos/aem-evolve-multi-agent-api/adversarial_tests"

CHECKS = [
    # v1.1 verification suite
    {
        "check_id": "V1_1-REGULATORY-MAPPING",
        "script":   TOOLS / "regulatory/regulatory_mapping_checker.py",
        "expected_status": "REGULATORY_MAPPING_CHECK=PASS",
    },
    {
        "check_id": "V1_1-GOVERNANCE-METRICS",
        "script":   TOOLS / "metrics/governance_effectiveness_metrics.py",
        "expected_status": "GOVERNANCE_EFFECTIVENESS_METRICS_STATUS=PASS",
    },
    {
        "check_id": "V1_1-MULTI-ANCHOR",
        "script":   TOOLS / "anchors/multi_anchor_verifier.py",
        "expected_status": "MULTI_ANCHOR_VERIFICATION=PASS",
    },
    {
        "check_id": "V1_1-HITL-SIGNATURE",
        "script":   TOOLS / "hitl/HITL_signature_verifier.py",
        "expected_status": "HITL_SIGNATURE_VERIFICATION=PASS_DEMO",
    },
    {
        "check_id": "V1_1-RECEIPT-FORGERY",
        "script":   ADV_TESTS / "test_receipt_forgery.py",
        "expected_status": "RECEIPT_FORGERY_TESTS=PASS",
    },
    {
        "check_id": "V1_1-OFFICIAL-STATUS",
        "script":   TOOLS / "status/official_status_signer.py",
        "expected_status": "OFFICIAL_STATUS_SIGNED=PASS",
    },
    # v1.2 verification suite
    {
        "check_id": "V1_2-MECH-REASON-ENGINE",
        "script":   TOOLS / "reasoning/mech_reason.py",
        "expected_status": "MECH_REASON_STATUS=PASS",
    },
    {
        "check_id": "V1_2-MECH-REASON-VERIFY",
        "script":   TOOLS / "reasoning/verify_mech_reason.py",
        "expected_status": "MECH_REASON_VERIFICATION=PASS",
    },
    # v1.3 verification suite
    {
        "check_id": "V1_3-LLM-ADVISORY",
        "script":   TOOLS / "advisory/llm_advisory_adapter.py",
        "expected_status": "LLM_ADVISORY_STATUS=PASS",
    },
    {
        "check_id": "V1_3-MLKEM768",
        "script":   TOOLS / "crypto/verify_mlkem768.py",
        "expected_status": "MLKEM768_STATUS=PASS",
    },
    {
        "check_id": "V1_3-HITL-QUORUM",
        "script":   TOOLS / "hitl/hitl_quorum_verifier.py",
        "expected_status": "HITL_QUORUM_VERIFICATION=PASS",
    },
    {
        "check_id": "V1_3-POSTGRES-ADAPTER",
        "script":   TOOLS / "db/validate_postgres_adapter.py",
        "expected_status": "POSTGRES_ADAPTER_VALIDATION=PASS",
    },
]


def run_check(check: dict) -> dict:
    script = check["script"]
    if not Path(script).exists():
        return {
            "check_id": check["check_id"],
            "status":   "FAIL",
            "detail":   f"script not found: {script}",
            "stdout":   "",
        }

    result = subprocess.run(
        [sys.executable, str(script)],
        capture_output=True, text=True, cwd=str(REPO_ROOT)
    )
    stdout   = result.stdout.strip()
    expected = check["expected_status"]
    passed   = expected in stdout

    return {
        "check_id": check["check_id"],
        "status":   "PASS" if passed else "FAIL",
        "detail":   f"expected '{expected}' in output — {'found' if passed else 'NOT FOUND'}",
        "stdout":   stdout[-300:] if len(stdout) > 300 else stdout,
    }


def main() -> int:
    print("[FULL-STACK REPRODUCTION VERIFIER] AEM-EVOLVE™ v1.3")
    print(f"  Running {len(CHECKS)} checks across v1.1 + v1.2 + v1.3 stacks...")

    results = []
    for check in CHECKS:
        r = run_check(check)
        mark = "✓" if r["status"] == "PASS" else "✗"
        print(f"  {mark} [{r['check_id']}] {r['detail']}")
        results.append(r)

    failed  = [r for r in results if r["status"] == "FAIL"]
    passed  = [r for r in results if r["status"] == "PASS"]
    overall = "PASS" if not failed else "FAIL"

    report = {
        "schema_id":          "AEM_EVOLVE_REPRODUCTION_REPORT_V1_3",
        "generated_at":       datetime.now(timezone.utc).isoformat(),
        "stack_versions":     ["v1.1", "v1.2", "v1.3"],
        "verification_result": overall,
        "checks_passed":      len(passed),
        "checks_failed":      len(failed),
        "total_checks":       len(CHECKS),
        "results":            results,
        "non_claims": [
            "This reproduction report is not a regulatory audit.",
            "This reproduction report is not external certification.",
            "This reproduction report does not replace HITL human review.",
            "Passing all checks does not constitute production readiness.",
        ],
    }

    V1_3.mkdir(parents=True, exist_ok=True)
    with open(REPORT_OUT, "w") as f:
        json.dump(report, f, indent=2)

    print(f"\n  Passed: {len(passed)}/{len(CHECKS)}")
    print(f"FULL_STACK_VERIFICATION={overall}")
    return 0 if overall == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
