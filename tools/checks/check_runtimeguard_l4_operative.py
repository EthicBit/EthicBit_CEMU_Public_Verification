#!/usr/bin/env python3
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

REQUIRED_FILES = [
    "artifacts/cases/case_003/runtime_constitutional_assessment.case_003.canonical.json",
    "artifacts/cases/case_003/freeze_decision.case_003.canonical.json",
    "cemu/builders/runtime_guard.py",
    "cemu/builders/runtime_guard_l4_policy.json",
    "cemu/builders/runtime_guard_l4_checklist.json",
    "assurance/in-toto/root.layout",
    "assurance/slsa/provenance.json",
    "assurance/slsa/level4-policy.json",
    "assurance/slsa/subject-index.json",
    "assurance/sigstore/policy.json",
    "regulatory/policies/regulatory_policy_baseline.json",
]

def main():
    results = []
    all_ok = True

    for rel in REQUIRED_FILES:
        exists = (ROOT / rel).exists()
        results.append({"path": rel, "exists": exists})
        if not exists:
            all_ok = False

    decision = {
        "schema_id": "ETHICBIT_RUNTIMEGUARD_L4_OPERATIVE_DECISION_V1",
        "case_id": "case_003",
        "status": "ALLOW_OPERATIVE_BASELINE" if all_ok else "BLOCK_OPERATIVE_BASELINE",
        "reason": "all_required_runtimeguard_l4_refs_present" if all_ok else "missing_required_runtimeguard_l4_refs",
    }

    block_record = {
        "schema_id": "ETHICBIT_RUNTIMEGUARD_L4_BLOCK_RECORD_V1",
        "case_id": "case_003",
        "status": "NOT_TRIGGERED" if all_ok else "FREEZE_REQUIRED",
        "trigger": None if all_ok else "runtimeguard_l4_missing_critical_reference",
    }

    report = {
        "check_id": "RUNTIMEGUARD_L4_OPERATIVE_CHECK",
        "status": "ALLOW_OPERATIVE_BASELINE" if all_ok else "BLOCK_OPERATIVE_BASELINE",
        "results": results,
        "decision_ref": "artifacts/cases/case_003/runtimeguard_l4_decision.case_003.json",
        "block_record_ref": "artifacts/cases/case_003/runtimeguard_l4_block_record.case_003.json",
    }

    decision_path = ROOT / "artifacts/cases/case_003/runtimeguard_l4_decision.case_003.json"
    block_path = ROOT / "artifacts/cases/case_003/runtimeguard_l4_block_record.case_003.json"
    report_path = ROOT / "reports/operative_checks/runtimeguard_l4_operative_check.json"
    log_path = ROOT / "logs/runtimeguard_l4_operative.log"

    decision_path.write_text(json.dumps(decision, indent=2), encoding="utf-8")
    block_path.write_text(json.dumps(block_record, indent=2), encoding="utf-8")
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    log_path.write_text(
        f"RUNTIMEGUARD_L4_OPERATIVE_CHECK={report['status']}\n"
        f"DECISION={decision['status']}\n"
        f"BLOCK_RECORD={block_record['status']}\n",
        encoding="utf-8"
    )

    print(json.dumps(report, indent=2))
    print(json.dumps(decision, indent=2))
    print(json.dumps(block_record, indent=2))

if __name__ == "__main__":
    main()
