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

TARGETS = [
    "local_controlled",
    "github_actions_runner",
    "distributed_target_placeholder",
]

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

    target_results = []
    if all_ok:
        env_registry = load_json("deployment/environments/environment_registry.json")
        target_matrix = load_json("deployment/manifests/distributed_target_matrix.json")

        envs = {item["environment_id"]: item for item in env_registry.get("environments", [])}
        targets = {item["target_id"]: item for item in target_matrix.get("targets", [])}

        for tid in TARGETS:
            target_present = tid in targets
            env_ref_present = False
            human_review_required = False

            if target_present:
                env_ref = targets[tid].get("environment_ref")
                env_ref_present = env_ref == "deployment/environments/environment_registry.json"
                human_review_required = bool(targets[tid].get("human_review_required", False))

            ok = target_present and env_ref_present and human_review_required
            if not ok:
                all_ok = False

            target_results.append({
                "target_id": tid,
                "target_present": target_present,
                "environment_ref_present": env_ref_present,
                "human_review_required": human_review_required,
                "status": "PASS_OPERATIVE_BASELINE" if ok else "FAIL_OPERATIVE_BASELINE"
            })

    certification_report = {
        "schema_id": "ETHICBIT_DISTRIBUTED_PRODUCTION_CERTIFICATION_REPORT_V1",
        "status": "PASS_OPERATIVE_BASELINE" if all_ok else "FAIL_OPERATIVE_BASELINE",
        "targets": target_results
    }

    report = {
        "check_id": "DISTRIBUTED_PRODUCTION_OPERATIVE_CHECK",
        "status": "PASS_OPERATIVE_BASELINE" if all_ok else "FAIL_OPERATIVE_BASELINE",
        "results": results,
        "target_results": target_results,
        "certification_report_ref": "audit/deployment/distributed_production_certification_report.json"
    }

    report_path = ROOT / "reports/operative_checks/distributed_production_operative_check.json"
    cert_path = ROOT / "audit/deployment/distributed_production_certification_report.json"
    log_path = ROOT / "logs/distributed_production_operative.log"

    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    cert_path.write_text(json.dumps(certification_report, indent=2), encoding="utf-8")
    log_path.write_text(
        f"DISTRIBUTED_PRODUCTION_OPERATIVE_CHECK={report['status']}\n" +
        "\n".join(f"{t['target_id']}={t['status']}" for t in target_results),
        encoding="utf-8"
    )

    print(json.dumps(report, indent=2))
    print(json.dumps(certification_report, indent=2))

if __name__ == "__main__":
    main()
