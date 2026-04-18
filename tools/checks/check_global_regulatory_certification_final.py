#!/usr/bin/env python3
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

REPORTS = [
    ("US", "audit/regulatory/US_certification_report.json"),
    ("EU", "audit/regulatory/EU_certification_report.json"),
    ("UK", "audit/regulatory/UK_certification_report.json"),
    ("CO", "audit/regulatory/CO_certification_report.json"),
]

VALID_PASS = {"CERTIFICATION_GRANTED", "CERTIFICATION_GRANTED_WITH_LIMITS"}

def load_json(rel_path: str):
    return json.loads((ROOT / rel_path).read_text(encoding="utf-8"))

def main():
    checks = []
    final_ok = True

    for jid, rel in REPORTS:
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
            "jurisdiction_id": jid,
            "report": rel,
            "exists": exists,
            "actual_status": actual,
            "status": "PASS_CERTIFICATION_FINAL" if ok else "FAIL_CERTIFICATION_FINAL"
        })

    consolidated = {
        "schema_id": "ETHICBIT_GLOBAL_REGULATORY_CERTIFICATION_REPORT_V2",
        "status": "PASS_CERTIFICATION_FINAL" if final_ok else "FAIL_CERTIFICATION_FINAL",
        "jurisdictions": checks
    }

    report = {
        "check_id": "GLOBAL_REGULATORY_CERTIFICATION_FINAL_CHECK",
        "status": "PASS_CERTIFICATION_FINAL" if final_ok else "FAIL_CERTIFICATION_FINAL",
        "checks": checks,
        "consolidated_report_ref": "audit/regulatory/global_regulatory_certification_report.json"
    }

    report_path = ROOT / "reports/final_checks/global_regulatory_certification_final_check.json"
    consolidated_path = ROOT / "audit/regulatory/global_regulatory_certification_report.json"
    log_path = ROOT / "logs/global_regulatory_certification_final.log"

    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    consolidated_path.write_text(json.dumps(consolidated, indent=2), encoding="utf-8")
    log_path.write_text(
        f"GLOBAL_REGULATORY_CERTIFICATION_FINAL_CHECK={report['status']}\n" +
        "\n".join(f"{c['jurisdiction_id']}={c['status']}" for c in checks),
        encoding="utf-8"
    )

    print(json.dumps(report, indent=2))
    print(json.dumps(consolidated, indent=2))

if __name__ == "__main__":
    main()
