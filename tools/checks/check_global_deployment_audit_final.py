#!/usr/bin/env python3
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

REPORTS = [
    "audit/deployment/local_controlled_audit_report.json",
    "audit/deployment/github_actions_runner_audit_report.json",
    "audit/deployment/distributed_target_01_audit_report.json",
    "audit/deployment/distributed_target_02_audit_report.json",
]

def load_json(rel_path: str):
    return json.loads((ROOT / rel_path).read_text(encoding="utf-8"))

def main():
    checks = []
    final_ok = True

    for rel in REPORTS:
        path = ROOT / rel
        exists = path.exists()
        status = None
        ok = False

        if exists:
            data = load_json(rel)
            status = data.get("status")
            ok = status == "PASS_AUDIT"

        if not ok:
            final_ok = False

        checks.append({
            "report": rel,
            "exists": exists,
            "actual_status": status,
            "status": "PASS_AUDIT_FINAL" if ok else "FAIL_AUDIT_FINAL"
        })

    consolidated = {
        "schema_id": "ETHICBIT_GLOBAL_DEPLOYMENT_AUDIT_REPORT_V2",
        "status": "PASS_AUDIT_FINAL" if final_ok else "FAIL_AUDIT_FINAL",
        "target_reports": checks
    }

    report = {
        "check_id": "GLOBAL_DEPLOYMENT_AUDIT_FINAL_CHECK",
        "status": "PASS_AUDIT_FINAL" if final_ok else "FAIL_AUDIT_FINAL",
        "checks": checks,
        "consolidated_report_ref": "audit/deployment/global_deployment_audit_report.json"
    }

    report_path = ROOT / "reports/final_checks/global_deployment_audit_final_check.json"
    consolidated_path = ROOT / "audit/deployment/global_deployment_audit_report.json"
    log_path = ROOT / "logs/global_deployment_audit_final.log"

    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    consolidated_path.write_text(json.dumps(consolidated, indent=2), encoding="utf-8")
    log_path.write_text(
        f"GLOBAL_DEPLOYMENT_AUDIT_FINAL_CHECK={report['status']}\n" +
        "\n".join(f"{c['report']}={c['status']}" for c in checks),
        encoding="utf-8"
    )

    print(json.dumps(report, indent=2))
    print(json.dumps(consolidated, indent=2))

if __name__ == "__main__":
    main()
