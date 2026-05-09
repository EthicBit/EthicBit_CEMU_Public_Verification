#!/usr/bin/env python3
"""Full-stack independent reproduction verifier — AEM-EVOLVE™ v1.4.

Runs all v1.1 + v1.2 + v1.3 + v1.4 verification scripts end-to-end and emits
a single FULL_STACK_VERIFICATION=PASS | FAIL with per-component results.

Designed for independent reproducers — anyone cloning this repository
can run this script to verify the entire AEM-EVOLVE™ assurance stack.

Requirements: Python >= 3.11, cryptography, mlkem, asyncpg  (see Dockerfile.reproduction)

Output: FULL_STACK_VERIFICATION=PASS (14/14) | FAIL
"""

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT  = Path(__file__).resolve().parents[4]
V1_4       = REPO_ROOT / "assurance/evolve-multi-agent/v1_4"
REPORT_OUT = V1_4 / "REPRODUCTION_REPORT.json"
TOOLS      = REPO_ROOT / "demos/aem-evolve-multi-agent-api/tools"
ADV_TESTS  = REPO_ROOT / "demos/aem-evolve-multi-agent-api/adversarial_tests"

CHECKS = [
    # ── v1.1 verification suite ───────────────────────────────────────────────
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
    # ── v1.2 verification suite ───────────────────────────────────────────────
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
    # ── v1.3 verification suite ───────────────────────────────────────────────
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
    # ── v1.4 verification suite ───────────────────────────────────────────────
    {
        "check_id": "V1_4-SIGNING-PROVIDER",
        "script":   TOOLS / "signing/verify_signing_provider.py",
        "expected_status": "SIGNING_PROVIDER_VERIFICATION=PASS",
    },
    {
        "check_id": "V1_4-HITL-IDENTITY",
        "script":   TOOLS / "hitl/hitl_identity_verifier.py",
        "expected_status": "HITL_IDENTITY_VERIFICATION=PASS",
    },
]


def _run_check(check: dict) -> dict:
    script = Path(check["script"])
    if not script.exists():
        return {
            **check,
            "result": "FAIL",
            "reason": f"script not found: {script}",
            "stdout": "",
        }
    result = subprocess.run(
        [sys.executable, str(script)],
        capture_output=True,
        text=True,
        timeout=120,
    )
    stdout = result.stdout + result.stderr
    passed = check["expected_status"] in stdout
    return {
        **check,
        "script": str(script),
        "result": "PASS" if passed else "FAIL",
        "exit_code": result.returncode,
        "stdout": stdout[-2000:],
    }


def main() -> int:
    print("AEM-EVOLVE™ v1.4 Full-Stack Verification")
    print("=" * 52)
    results = []
    passed = 0
    total = len(CHECKS)

    for check in CHECKS:
        res = _run_check(check)
        results.append(res)
        status = res["result"]
        if status == "PASS":
            passed += 1
        print(f"  {status}  {check['check_id']}")

    print()
    v1_1_p = sum(1 for r in results[:6]  if r["result"] == "PASS")
    v1_2_p = sum(1 for r in results[6:8]  if r["result"] == "PASS")
    v1_3_p = sum(1 for r in results[8:12] if r["result"] == "PASS")
    v1_4_p = sum(1 for r in results[12:]  if r["result"] == "PASS")
    print(f"  v1.1: {v1_1_p}/6  ·  v1.2: {v1_2_p}/2  ·  v1.3: {v1_3_p}/4  ·  v1.4: {v1_4_p}/2")

    overall = "PASS" if passed == total else "FAIL"
    report = {
        "version": "v1.4",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "result": overall,
        "checks_passed": passed,
        "checks_total": total,
        "non_claims": [
            "SigningProvider is not HSM-backed.",
            "HITL identity is not enterprise IAM.",
            "HITL tokens are not production-grade without external IdP.",
            "AsyncPostgresAdapter is not production-tested at scale.",
            "ML-KEM768 is not independently audited.",
            "CI reproduction is not external independent reproduction.",
            "This release is not regulatory approval.",
            "This release is not external certification.",
        ],
        "checks": results,
    }

    V1_4.mkdir(parents=True, exist_ok=True)
    REPORT_OUT.write_text(json.dumps(report, indent=2))
    print(f"\nFULL_STACK_VERIFICATION={overall}  ({passed}/{total})")
    return 0 if overall == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
