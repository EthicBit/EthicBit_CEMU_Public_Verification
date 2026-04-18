#!/usr/bin/env python3
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

REQUIRED_REPORTS = [
    ("reports/operative_checks/slsa_l4_operative_check.json", "PASS_OPERATIVE_BASELINE"),
    ("reports/operative_checks/multi_jurisdiction_operative_check.json", "PASS_OPERATIVE_BASELINE"),
    ("reports/operative_checks/distributed_production_operative_check.json", "PASS_OPERATIVE_BASELINE"),
    ("reports/final_checks/global_deployment_audit_final_check.json", "PASS_AUDIT_FINAL"),
    ("reports/final_checks/global_regulatory_certification_final_check.json", "PASS_CERTIFICATION_FINAL"),
]

RUNTIMEGUARD_NEGATIVE_REPORT = "reports/final_checks/runtimeguard_l4_negative_check.json"
RUNTIMEGUARD_NEGATIVE_DECISION = "artifacts/cases/case_003/runtimeguard_l4_negative_decision.case_003.json"
RUNTIMEGUARD_NEGATIVE_BLOCK = "artifacts/cases/case_003/runtimeguard_l4_negative_block_record.case_003.json"
APPROVAL_RECORD = "artifacts/production_final_approval_record.json"

def load_json(rel_path: str):
    return json.loads((ROOT / rel_path).read_text(encoding="utf-8"))

def main():
    checks = []
    ready = True

    approval_exists = (ROOT / APPROVAL_RECORD).exists()
    checks.append({
        "type": "required_file",
        "path": APPROVAL_RECORD,
        "exists": approval_exists,
        "status": "PASS_FINAL" if approval_exists else "FAIL_FINAL"
    })
    if not approval_exists:
        ready = False

    for rel, expected in REQUIRED_REPORTS:
        path = ROOT / rel
        exists = path.exists()
        actual = None
        ok = False
        if exists:
            data = load_json(rel)
            actual = data.get("status")
            ok = actual == expected
        if not ok:
            ready = False
        checks.append({
            "type": "required_report",
            "path": rel,
            "exists": exists,
            "expected_status": expected,
            "actual_status": actual,
            "status": "PASS_FINAL" if ok else "FAIL_FINAL"
        })

    neg_report_exists = (ROOT / RUNTIMEGUARD_NEGATIVE_REPORT).exists()
    neg_decision_exists = (ROOT / RUNTIMEGUARD_NEGATIVE_DECISION).exists()
    neg_block_exists = (ROOT / RUNTIMEGUARD_NEGATIVE_BLOCK).exists()

    neg_report_status = None
    neg_decision_status = None
    neg_block_status = None

    if neg_report_exists:
        neg_report_status = load_json(RUNTIMEGUARD_NEGATIVE_REPORT).get("status")
    if neg_decision_exists:
        neg_decision_status = load_json(RUNTIMEGUARD_NEGATIVE_DECISION).get("status")
    if neg_block_exists:
        neg_block_status = load_json(RUNTIMEGUARD_NEGATIVE_BLOCK).get("status")

    runtimeguard_negative_ok = (
        neg_report_exists and neg_report_status == "PASS_NEGATIVE_TEST" and
        neg_decision_exists and neg_decision_status == "BLOCK" and
        neg_block_exists and neg_block_status == "FREEZE_REQUIRED"
    )

    checks.append({
        "type": "runtimeguard_negative_enforcement",
        "path": RUNTIMEGUARD_NEGATIVE_REPORT,
        "exists": neg_report_exists,
        "negative_report_status": neg_report_status,
        "negative_decision_status": neg_decision_status,
        "negative_block_status": neg_block_status,
        "status": "FAIL_FINAL" if runtimeguard_negative_ok else "PASS_FINAL"
    })

    # If RuntimeGuard negative path is confirmed, readiness must NOT be ready.
    if runtimeguard_negative_ok:
        ready = False

    final_status = "READY_FINAL" if ready else "NOT_READY_FINAL"

    report = {
        "check_id": "PRODUCTION_DISTRIBUTED_READY_NEGATIVE_CHECK",
        "status": final_status,
        "checks": checks,
        "reason": "runtimeguard_negative_path_blocks_final_readiness" if runtimeguard_negative_ok else "no_blocking_negative_path_detected"
    }

    certificate = {
        "schema_id": "ETHICBIT_PRODUCTION_DISTRIBUTED_READINESS_NEGATIVE_CERTIFICATE_V1",
        "status": final_status,
        "basis": "negative_runtimeguard_path_enforced"
    }

    report_path = ROOT / "reports/final_checks/production_distributed_ready_negative_check.json"
    cert_path = ROOT / "artifacts/production_distributed_readiness_negative_certificate.json"
    log_path = ROOT / "logs/production_distributed_ready_negative.log"

    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    cert_path.write_text(json.dumps(certificate, indent=2), encoding="utf-8")
    log_path.write_text(
        f"PRODUCTION_DISTRIBUTED_READY_NEGATIVE_CHECK={report['status']}\n"
        f"RUNTIMEGUARD_NEGATIVE_ENFORCED={runtimeguard_negative_ok}\n",
        encoding="utf-8"
    )

    print(json.dumps(report, indent=2))
    print(json.dumps(certificate, indent=2))

if __name__ == "__main__":
    main()
