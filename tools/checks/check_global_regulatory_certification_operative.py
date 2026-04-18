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
    "audit/regulatory/global_regulatory_certification_matrix.json",
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

    jurisdiction_reports = []
    if all_ok:
        registry_data = load_json("regulatory/jurisdictions/jurisdiction_registry.json")
        coverage_data = load_json("regulatory/mappings/jurisdiction_coverage_matrix.json")
        cert_matrix = load_json("audit/regulatory/global_regulatory_certification_matrix.json")

        registry = {item["jurisdiction_id"]: item for item in registry_data.get("jurisdictions", [])}
        coverage = {item["jurisdiction_id"]: item for item in coverage_data.get("coverage", [])}
        certification = {item["jurisdiction_id"]: item for item in cert_matrix.get("jurisdictions", [])}

        for jid in TARGET_JURISDICTIONS:
            in_registry = jid in registry
            in_coverage = jid in coverage
            in_cert_matrix = jid in certification
            baseline_cert_status = certification.get(jid, {}).get("certification_status") == "BASELINE_REFERENCE_ONLY"
            human_review_required = coverage.get(jid, {}).get("human_review_required", False) if in_coverage else False

            ok = in_registry and in_coverage and in_cert_matrix and baseline_cert_status and human_review_required
            if not ok:
                all_ok = False

            jurisdiction_reports.append({
                "jurisdiction_id": jid,
                "in_registry": in_registry,
                "in_coverage_matrix": in_coverage,
                "in_certification_matrix": in_cert_matrix,
                "baseline_cert_status": baseline_cert_status,
                "human_review_required": human_review_required,
                "status": "PASS_OPERATIVE_BASELINE" if ok else "FAIL_OPERATIVE_BASELINE"
            })

    certification_report = {
        "schema_id": "ETHICBIT_GLOBAL_REGULATORY_CERTIFICATION_REPORT_V1",
        "status": "PASS_OPERATIVE_BASELINE" if all_ok else "FAIL_OPERATIVE_BASELINE",
        "jurisdictions": jurisdiction_reports
    }

    report = {
        "check_id": "GLOBAL_REGULATORY_CERTIFICATION_OPERATIVE_CHECK",
        "status": "PASS_OPERATIVE_BASELINE" if all_ok else "FAIL_OPERATIVE_BASELINE",
        "results": results,
        "jurisdiction_reports": jurisdiction_reports,
        "certification_report_ref": "audit/regulatory/global_regulatory_certification_report.json"
    }

    report_path = ROOT / "reports/operative_checks/global_regulatory_certification_operative_check.json"
    cert_report_path = ROOT / "audit/regulatory/global_regulatory_certification_report.json"
    log_path = ROOT / "logs/global_regulatory_certification_operative.log"

    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    cert_report_path.write_text(json.dumps(certification_report, indent=2), encoding="utf-8")
    log_path.write_text(
        f"GLOBAL_REGULATORY_CERTIFICATION_OPERATIVE_CHECK={report['status']}\n" +
        "\n".join(f"{j['jurisdiction_id']}={j['status']}" for j in jurisdiction_reports),
        encoding="utf-8"
    )

    print(json.dumps(report, indent=2))
    print(json.dumps(certification_report, indent=2))

if __name__ == "__main__":
    main()
