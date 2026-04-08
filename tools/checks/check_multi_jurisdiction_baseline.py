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

def main():
    results = []
    all_ok = True

    for rel in REQUIRED_FILES:
        exists = (ROOT / rel).exists()
        results.append({"path": rel, "exists": exists})
        if not exists:
            all_ok = False

    out = {
        "check_id": "MULTI_JURISDICTION_BASELINE_CHECK",
        "status": "PASS_BASELINE" if all_ok else "FAIL_BASELINE",
        "results": results,
    }

    out_path = ROOT / "reports/baseline_checks/multi_jurisdiction_baseline_check.json"
    out_path.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(json.dumps(out, indent=2))

if __name__ == "__main__":
    main()
