#!/usr/bin/env python3
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

REQUIRED_REPORTS = [
    ("reports/operative_checks/slsa_l4_operative_check.json", "PASS_OPERATIVE_BASELINE"),
    ("reports/operative_checks/runtimeguard_l4_operative_check.json", "ALLOW_OPERATIVE_BASELINE"),
    ("reports/operative_checks/multi_jurisdiction_operative_check.json", "PASS_OPERATIVE_BASELINE"),
    ("reports/operative_checks/distributed_production_operative_check.json", "PASS_OPERATIVE_BASELINE"),
    ("reports/final_checks/global_deployment_audit_final_check.json", "PASS_AUDIT_FINAL"),
    ("reports/final_checks/global_regulatory_certification_final_check.json", "PASS_CERTIFICATION_FINAL"),
]

REQUIRED_FILES = [
    "artifacts/production_final_approval_record.json",
]

def load_json(rel_path: str):
    return json.loads((ROOT / rel_path).read_text(encoding="utf-8"))

def main():
    checks = []
    ready = True

    for rel in REQUIRED_FILES:
        path = ROOT / rel
        exists = path.exists()
        if not exists:
            ready = False
        checks.append({
            "type": "required_file",
            "path": rel,
            "exists": exists,
            "status": "PASS_FINAL" if exists else "FAIL_FINAL"
        })

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

    final_decision = {
        "schema_id": "ETHICBIT_PRODUCTION_DISTRIBUTED_READY_FINAL_DECISION_V1",
        "status": "READY_FINAL" if ready else "NOT_READY_FINAL",
        "human_review_required": True,
        "basis": "final_reports_and_final_approval"
    }

    readiness_certificate = {
        "schema_id": "ETHICBIT_PRODUCTION_DISTRIBUTED_READINESS_CERTIFICATE_FINAL_V1",
        "status": final_decision["status"],
        "basis": "final_check_gate",
        "human_review_required": True
    }

    report = {
        "check_id": "PRODUCTION_DISTRIBUTED_READY_FINAL_CHECK",
        "status": final_decision["status"],
        "checks": checks,
        "final_decision_ref": "artifacts/production_distributed_readiness_certificate_final.json"
    }

    report_path = ROOT / "reports/final_checks/production_distributed_ready_final_check.json"
    cert_path = ROOT / "artifacts/production_distributed_readiness_certificate_final.json"
    log_path = ROOT / "logs/production_distributed_ready_final.log"

    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    cert_path.write_text(json.dumps(readiness_certificate, indent=2), encoding="utf-8")
    log_path.write_text(
        f"PRODUCTION_DISTRIBUTED_READY_FINAL_CHECK={report['status']}\n" +
        "\n".join(f"{c['path']}={c['status']}" for c in checks),
        encoding="utf-8"
    )

    print(json.dumps(report, indent=2))
    print(json.dumps(readiness_certificate, indent=2))
    if not ready:
        raise SystemExit(1)

if __name__ == "__main__":
    main()
