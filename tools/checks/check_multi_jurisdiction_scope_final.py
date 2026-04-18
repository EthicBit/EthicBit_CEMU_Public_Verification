#!/usr/bin/env python3
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

REQUIRED = [
    "regulatory/jurisdictions/final_scope_v10.0.json",
    "audit/regulatory/US_certification_report.json",
    "audit/regulatory/EU_certification_report.json",
    "audit/regulatory/UK_certification_report.json",
    "audit/regulatory/CO_certification_report.json",
    "reports/final_checks/global_regulatory_certification_final_check.json",
]

EXPECTED_SCOPE = {"US", "EU", "UK", "CO"}
VALID_PASS = {"CERTIFICATION_GRANTED", "CERTIFICATION_GRANTED_WITH_LIMITS"}

def load_json(rel):
    return json.loads((ROOT / rel).read_text(encoding="utf-8"))

def main():
    checks = []
    ok = True

    for rel in REQUIRED:
        exists = (ROOT / rel).exists()
        checks.append({
            "type": "required_file",
            "path": rel,
            "exists": exists,
            "status": "PASS_FINAL" if exists else "FAIL_FINAL"
        })
        if not exists:
            ok = False

    if ok:
        scope = load_json("regulatory/jurisdictions/final_scope_v10.0.json")
        scope_set = set(scope.get("jurisdictions_in_scope", []))
        scope_closed = scope.get("scope_type") == "CLOSED_SCOPE"
        scope_ok = scope_set == EXPECTED_SCOPE and scope_closed
        if not scope_ok:
            ok = False
        checks.append({
            "type": "scope_definition",
            "scope_type": scope.get("scope_type"),
            "scope_set": sorted(scope_set),
            "expected_scope": sorted(EXPECTED_SCOPE),
            "status": "PASS_FINAL" if scope_ok else "FAIL_FINAL"
        })

        for jid in sorted(EXPECTED_SCOPE):
            rep = load_json(f"audit/regulatory/{jid}_certification_report.json")
            status = rep.get("status")
            pass_ok = status in VALID_PASS
            if not pass_ok:
                ok = False
            checks.append({
                "type": "jurisdiction_certification",
                "jurisdiction_id": jid,
                "actual_status": status,
                "status": "PASS_FINAL" if pass_ok else "FAIL_FINAL"
            })

        global_final = load_json("reports/final_checks/global_regulatory_certification_final_check.json")
        global_ok = global_final.get("status") == "PASS_CERTIFICATION_FINAL"
        if not global_ok:
            ok = False
        checks.append({
            "type": "global_certification_final",
            "actual_status": global_final.get("status"),
            "status": "PASS_FINAL" if global_ok else "FAIL_FINAL"
        })

    report = {
        "check_id": "MULTI_JURISDICTION_SCOPE_FINAL_CHECK",
        "status": "PASS_SCOPE_FINAL" if ok else "FAIL_SCOPE_FINAL",
        "rule": "Support is complete only for the closed declared scope.",
        "checks": checks
    }

    decision = {
        "schema_id": "ETHICBIT_MULTI_JURISDICTION_COMPLETE_DECISION_V1",
        "status": "MULTI_JURISDICTIONAL_SUPPORT_COMPLETE" if ok else "MULTI_JURISDICTIONAL_SUPPORT_NOT_COMPLETE",
        "scope_ref": "regulatory/jurisdictions/final_scope_v10.0.json"
    }

    report_path = ROOT / "reports/final_checks/multi_jurisdiction_scope_final_check.json"
    decision_path = ROOT / "audit/regulatory/multi_jurisdiction_complete_decision.json"
    log_path = ROOT / "logs/multi_jurisdiction_scope_final.log"

    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    decision_path.write_text(json.dumps(decision, indent=2), encoding="utf-8")
    log_path.write_text(
        f"MULTI_JURISDICTION_SCOPE_FINAL_CHECK={report['status']}\n"
        f"DECISION={decision['status']}\n",
        encoding="utf-8"
    )

    print(json.dumps(report, indent=2))
    print(json.dumps(decision, indent=2))

if __name__ == "__main__":
    main()
