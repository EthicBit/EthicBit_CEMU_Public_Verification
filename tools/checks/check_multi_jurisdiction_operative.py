#!/usr/bin/env python3
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

REQUIRED_FILES = [
    "regulatory/jurisdictions/jurisdiction_registry.json",
    "regulatory/mappings/ceerv_regulatory_mapping.json",
    "regulatory/mappings/jurisdiction_coverage_matrix.json",
    "regulatory/policies/regulatory_policy_baseline.json",
    "regulatory/policies/jurisdiction_escalation_policy.json",
]

TARGET_JURISDICTIONS = ["US", "EU", "UK", "CO"]

def load_json(rel_path: str):
    return json.loads((ROOT / rel_path).read_text(encoding="utf-8"))

def main():
    results = []
    all_ok = True

    for rel in REQUIRED_FILES:
        exists = (ROOT / rel).exists()
        results.append({"path": rel, "exists": exists})
        if not exists:
            all_ok = False

    registry = {}
    coverage = {}
    if all_ok:
        registry_data = load_json("regulatory/jurisdictions/jurisdiction_registry.json")
        coverage_data = load_json("regulatory/mappings/jurisdiction_coverage_matrix.json")

        registry = {
            item["jurisdiction_id"]: item
            for item in registry_data.get("jurisdictions", [])
        }
        coverage = {
            item["jurisdiction_id"]: item
            for item in coverage_data.get("coverage", [])
        }

    jurisdiction_results = []
    if all_ok:
        for jid in TARGET_JURISDICTIONS:
            in_registry = jid in registry
            in_coverage = jid in coverage
            human_review_required = coverage.get(jid, {}).get("human_review_required", False) if in_coverage else False

            ok = in_registry and in_coverage and human_review_required
            if not ok:
                all_ok = False

            jurisdiction_results.append({
                "jurisdiction_id": jid,
                "in_registry": in_registry,
                "in_coverage_matrix": in_coverage,
                "human_review_required": human_review_required,
                "status": "PASS_OPERATIVE_BASELINE" if ok else "FAIL_OPERATIVE_BASELINE"
            })

    support_report = {
        "schema_id": "ETHICBIT_MULTI_JURISDICTION_SUPPORT_REPORT_V1",
        "status": "PASS_OPERATIVE_BASELINE" if all_ok else "FAIL_OPERATIVE_BASELINE",
        "jurisdictions": jurisdiction_results
    }

    report = {
        "check_id": "MULTI_JURISDICTION_OPERATIVE_CHECK",
        "status": "PASS_OPERATIVE_BASELINE" if all_ok else "FAIL_OPERATIVE_BASELINE",
        "results": results,
        "jurisdiction_results": jurisdiction_results,
        "support_report_ref": "audit/regulatory/multi_jurisdiction_support_report.json"
    }

    report_path = ROOT / "reports/operative_checks/multi_jurisdiction_operative_check.json"
    support_path = ROOT / "audit/regulatory/multi_jurisdiction_support_report.json"
    log_path = ROOT / "logs/multi_jurisdiction_operative.log"

    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    support_path.write_text(json.dumps(support_report, indent=2), encoding="utf-8")
    log_path.write_text(
        f"MULTI_JURISDICTION_OPERATIVE_CHECK={report['status']}\n" +
        "\n".join(f"{j['jurisdiction_id']}={j['status']}" for j in jurisdiction_results),
        encoding="utf-8"
    )

    print(json.dumps(report, indent=2))
    print(json.dumps(support_report, indent=2))

if __name__ == "__main__":
    main()
