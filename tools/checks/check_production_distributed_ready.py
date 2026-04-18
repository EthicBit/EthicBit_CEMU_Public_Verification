#!/usr/bin/env python3
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

REQUIRED_REPORTS = [
    ("reports/operative_checks/slsa_l4_operative_check.json", "PASS_OPERATIVE_BASELINE"),
    ("reports/operative_checks/runtimeguard_l4_operative_check.json", "ALLOW_OPERATIVE_BASELINE"),
    ("reports/operative_checks/multi_jurisdiction_operative_check.json", "PASS_OPERATIVE_BASELINE"),
    ("reports/operative_checks/distributed_production_operative_check.json", "PASS_OPERATIVE_BASELINE"),
    ("reports/operative_checks/global_deployment_audit_operative_check.json", "PASS_OPERATIVE_BASELINE"),
    ("reports/operative_checks/global_regulatory_certification_operative_check.json", "PASS_OPERATIVE_BASELINE"),
]

def load_json(rel_path: str):
    return json.loads((ROOT / rel_path).read_text(encoding="utf-8"))

def main():
    checks = []
    ready = True

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
            "report": rel,
            "exists": exists,
            "expected_status": expected,
            "actual_status": actual,
            "status": "PASS_OPERATIVE_BASELINE" if ok else "FAIL_OPERATIVE_BASELINE"
        })

    final_decision = {
        "schema_id": "ETHICBIT_PRODUCTION_DISTRIBUTED_READY_DECISION_V1",
        "status": "READY_OPERATIVE_BASELINE" if ready else "NOT_READY_OPERATIVE_BASELINE",
        "human_review_required": True,
        "checks_ref": "reports/operative_checks/production_distributed_ready_check.json"
    }

    report = {
        "check_id": "PRODUCTION_DISTRIBUTED_READY_CHECK",
        "status": "READY_OPERATIVE_BASELINE" if ready else "NOT_READY_OPERATIVE_BASELINE",
        "checks": checks,
        "final_decision_ref": "artifacts/production_distributed_readiness_certificate.json"
    }

    cert = {
        "schema_id": "ETHICBIT_PRODUCTION_DISTRIBUTED_READINESS_CERTIFICATE_V1",
        "status": report["status"],
        "basis": "operative_baseline_reports",
        "human_review_required": True
    }

    report_path = ROOT / "reports/operative_checks/production_distributed_ready_check.json"
    cert_path = ROOT / "artifacts/production_distributed_readiness_certificate.json"
    log_path = ROOT / "logs/production_distributed_ready.log"

    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    cert_path.write_text(json.dumps(cert, indent=2), encoding="utf-8")
    log_path.write_text(
        f"PRODUCTION_DISTRIBUTED_READY_CHECK={report['status']}\n" +
        "\n".join(f"{c['report']}={c['status']}" for c in checks),
        encoding="utf-8"
    )

    print(json.dumps(report, indent=2))
    print(json.dumps(cert, indent=2))

if __name__ == "__main__":
    main()
