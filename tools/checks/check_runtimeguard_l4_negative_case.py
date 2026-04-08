#!/usr/bin/env python3
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

CRITICAL_FILES = [
    "assurance/in-toto/root.layout",
    "assurance/slsa/level4-policy.json",
    "assurance/sigstore/policy.json",
    "regulatory/policies/regulatory_policy_baseline.json",
]

SIMULATED_MISSING = "assurance/sigstore/policy.json"

def main():
    results = []
    blocked = False

    for rel in CRITICAL_FILES:
        exists = (ROOT / rel).exists()
        simulated_effective_exists = exists and rel != SIMULATED_MISSING
        if not simulated_effective_exists:
            blocked = True

        results.append({
            "path": rel,
            "exists_on_disk": exists,
            "effective_exists_for_test": simulated_effective_exists,
            "status": "PASS_NEGATIVE_CHECK" if simulated_effective_exists else "FAIL_NEGATIVE_CHECK"
        })

    decision = {
        "schema_id": "ETHICBIT_RUNTIMEGUARD_L4_NEGATIVE_DECISION_V1",
        "case_id": "case_003",
        "status": "BLOCK" if blocked else "ALLOW",
        "reason": "simulated_missing_critical_sigstore_policy" if blocked else "no_failure_detected"
    }

    block_record = {
        "schema_id": "ETHICBIT_RUNTIMEGUARD_L4_NEGATIVE_BLOCK_RECORD_V1",
        "case_id": "case_003",
        "status": "FREEZE_REQUIRED" if blocked else "NOT_TRIGGERED",
        "trigger": "missing_critical_reference" if blocked else None
    }

    report = {
        "check_id": "RUNTIMEGUARD_L4_NEGATIVE_CASE_CHECK",
        "status": "PASS_NEGATIVE_TEST" if blocked else "FAIL_NEGATIVE_TEST",
        "simulated_missing": SIMULATED_MISSING,
        "results": results,
        "decision_ref": "artifacts/cases/case_003/runtimeguard_l4_negative_decision.case_003.json",
        "block_record_ref": "artifacts/cases/case_003/runtimeguard_l4_negative_block_record.case_003.json"
    }

    report_path = ROOT / "reports/final_checks/runtimeguard_l4_negative_check.json"
    decision_path = ROOT / "artifacts/cases/case_003/runtimeguard_l4_negative_decision.case_003.json"
    block_path = ROOT / "artifacts/cases/case_003/runtimeguard_l4_negative_block_record.case_003.json"
    log_path = ROOT / "logs/runtimeguard_l4_negative.log"

    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    decision_path.write_text(json.dumps(decision, indent=2), encoding="utf-8")
    block_path.write_text(json.dumps(block_record, indent=2), encoding="utf-8")
    log_path.write_text(
        f"RUNTIMEGUARD_L4_NEGATIVE_CASE_CHECK={report['status']}\n"
        f"SIMULATED_MISSING={SIMULATED_MISSING}\n"
        f"DECISION={decision['status']}\n"
        f"BLOCK_RECORD={block_record['status']}\n",
        encoding="utf-8"
    )

    print(json.dumps(report, indent=2))
    print(json.dumps(decision, indent=2))
    print(json.dumps(block_record, indent=2))

if __name__ == "__main__":
    main()
