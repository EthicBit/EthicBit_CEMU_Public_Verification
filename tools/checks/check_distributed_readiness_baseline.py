#!/usr/bin/env python3
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

REQUIRED_FILES = [
    "deployment/environments/environment_registry.json",
    "deployment/manifests/distributed_release_manifest.json",
    "deployment/manifests/distributed_target_matrix.json",
    "deployment/policies/distributed_production_policy.json",
    "deployment/policies/distributed_readiness_checklist.json",
    "deployment/policies/production_distributed_readiness_gate.json",
    "audit/deployment/global_deployment_audit_index.json",
    "audit/regulatory/global_regulatory_certification_matrix.json",
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
        "check_id": "DISTRIBUTED_READINESS_BASELINE_CHECK",
        "status": "PASS_BASELINE" if all_ok else "FAIL_BASELINE",
        "results": results,
    }

    out_path = ROOT / "reports/baseline_checks/distributed_readiness_baseline_check.json"
    out_path.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(json.dumps(out, indent=2))

if __name__ == "__main__":
    main()
