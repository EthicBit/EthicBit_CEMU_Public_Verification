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
]

def load_json(rel_path: str):
    return json.loads((ROOT / rel_path).read_text(encoding="utf-8"))


def resolve_target_ids(target_matrix: dict) -> list[str]:
    targets = target_matrix.get("targets", [])
    if not isinstance(targets, list):
        return []
    ids: list[str] = []
    for item in targets:
        if not isinstance(item, dict):
            continue
        tid = item.get("target_id")
        if isinstance(tid, str) and tid.strip():
            ids.append(tid.strip())
    return ids

def main():
    results = []
    all_ok = True

    for rel in REQUIRED_FILES:
        exists = (ROOT / rel).exists()
        results.append({"path": rel, "exists": exists})
        if not exists:
            all_ok = False

    target_audits = []
    if all_ok:
        env_registry = load_json("deployment/environments/environment_registry.json")
        target_matrix = load_json("deployment/manifests/distributed_target_matrix.json")
        audit_index = load_json("audit/deployment/global_deployment_audit_index.json")

        envs = {
            item["environment_id"]: item
            for item in env_registry.get("environments", [])
            if isinstance(item, dict) and "environment_id" in item
        }
        targets = {
            item["target_id"]: item
            for item in target_matrix.get("targets", [])
            if isinstance(item, dict) and "target_id" in item
        }
        target_ids = resolve_target_ids(target_matrix)
        if not target_ids:
            all_ok = False
        audited_layers = audit_index.get("audited_layers", [])

        audit_index_present = len(audited_layers) > 0

        for tid in target_ids:
            target_present = tid in targets
            environment_known = tid in envs
            human_review_required = bool(targets.get(tid, {}).get("human_review_required", False))
            ok = target_present and environment_known and audit_index_present and human_review_required
            if not ok:
                all_ok = False

            target_audits.append({
                "target_id": tid,
                "target_present": target_present,
                "environment_known": environment_known,
                "audit_index_present": audit_index_present,
                "human_review_required": human_review_required,
                "status": "PASS_OPERATIVE_BASELINE" if ok else "FAIL_OPERATIVE_BASELINE"
            })

    global_report = {
        "schema_id": "ETHICBIT_GLOBAL_DEPLOYMENT_AUDIT_REPORT_V1",
        "status": "PASS_OPERATIVE_BASELINE" if all_ok else "FAIL_OPERATIVE_BASELINE",
        "targets": target_audits
    }

    report = {
        "check_id": "GLOBAL_DEPLOYMENT_AUDIT_OPERATIVE_CHECK",
        "status": "PASS_OPERATIVE_BASELINE" if all_ok else "FAIL_OPERATIVE_BASELINE",
        "results": results,
        "target_audits": target_audits,
        "global_audit_report_ref": "audit/deployment/global_deployment_audit_report.json"
    }

    report_path = ROOT / "reports/operative_checks/global_deployment_audit_operative_check.json"
    global_report_path = ROOT / "audit/deployment/global_deployment_audit_report.json"
    log_path = ROOT / "logs/global_deployment_audit_operative.log"

    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    global_report_path.write_text(json.dumps(global_report, indent=2), encoding="utf-8")
    log_path.write_text(
        f"GLOBAL_DEPLOYMENT_AUDIT_OPERATIVE_CHECK={report['status']}\n" +
        "\n".join(f"{t['target_id']}={t['status']}" for t in target_audits),
        encoding="utf-8"
    )

    print(json.dumps(report, indent=2))
    print(json.dumps(global_report, indent=2))

if __name__ == "__main__":
    main()
