#!/usr/bin/env python3
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

REPORTS = [
    ("local_controlled", "audit/deployment/local_controlled_certification_report.json"),
    ("github_actions_runner", "audit/deployment/github_actions_runner_certification_report.json"),
    ("distributed_target_01", "audit/deployment/distributed_target_01_certification_report.json"),
    ("distributed_target_02", "audit/deployment/distributed_target_02_certification_report.json"),
]

VALID_PASS = {"CERTIFIED_TARGET", "CERTIFIED_TARGET_WITH_LIMITS"}

def load_json(rel_path: str):
    return json.loads((ROOT / rel_path).read_text(encoding="utf-8"))

def main():
    checks = []
    final_ok = True

    for target_id, rel in REPORTS:
        path = ROOT / rel
        exists = path.exists()
        actual = None
        ok = False

        if exists:
            data = load_json(rel)
            actual = data.get("status")
            ok = actual in VALID_PASS

        if not ok:
            final_ok = False

        checks.append({
            "target_id": target_id,
            "report": rel,
            "exists": exists,
            "actual_status": actual,
            "status": "PASS_CERTIFICATION_FINAL" if ok else "FAIL_CERTIFICATION_FINAL"
        })

    consolidated = {
        "schema_id": "ETHICBIT_DISTRIBUTED_PRODUCTION_CERTIFICATION_REPORT_V2",
        "status": "PASS_CERTIFICATION_FINAL" if final_ok else "FAIL_CERTIFICATION_FINAL",
        "targets": checks
    }

    report = {
        "check_id": "DISTRIBUTED_PRODUCTION_CERTIFICATION_FINAL_CHECK",
        "status": "PASS_CERTIFICATION_FINAL" if final_ok else "FAIL_CERTIFICATION_FINAL",
        "checks": checks,
        "consolidated_report_ref": "audit/deployment/distributed_production_certification_report_final.json"
    }

    report_path = ROOT / "reports/final_checks/distributed_production_certification_final_check.json"
    consolidated_path = ROOT / "audit/deployment/distributed_production_certification_report_final.json"
    log_path = ROOT / "logs/distributed_production_certification_final.log"

    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    consolidated_path.write_text(json.dumps(consolidated, indent=2), encoding="utf-8")
    log_path.write_text(
        f"DISTRIBUTED_PRODUCTION_CERTIFICATION_FINAL_CHECK={report['status']}\n" +
        "\n".join(f"{c['target_id']}={c['status']}" for c in checks),
        encoding="utf-8"
    )

    print(json.dumps(report, indent=2))
    print(json.dumps(consolidated, indent=2))

if __name__ == "__main__":
    main()
