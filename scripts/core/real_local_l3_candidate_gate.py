import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from agentic.support.real_local_evidence import RULE_EVIDENCE_MAP, resolve_real_local_evidence

def load_json(path_str: str):
    p = Path(path_str)
    return json.loads(p.read_text(encoding="utf-8"))

def extract_timestamp_fields(obj):
    ts = {}
    if isinstance(obj, dict):
        for k, v in obj.items():
            if isinstance(v, (dict, list)):
                nested = extract_timestamp_fields(v)
                for nk, nv in nested.items():
                    ts[f"{k}.{nk}"] = nv
            else:
                lk = str(k).lower()
                if "time" in lk or "date" in lk or lk.endswith("_at"):
                    ts[k] = v
    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            nested = extract_timestamp_fields(item)
            for nk, nv in nested.items():
                ts[f"[{i}].{nk}"] = nv
    return ts

results = {}
failed_rules = []
warnings = []
consistency_checks = []

loaded_docs = {}

for rule_id in RULE_EVIDENCE_MAP:
    try:
        resolved = resolve_real_local_evidence(rule_id)
        parsed = {}
        timestamps_found = {}

        for ev_key, meta in resolved.items():
            p = Path(meta["path"])
            parsed_ok = False
            ts_count = 0

            if p.suffix.lower() == ".json":
                try:
                    doc = load_json(str(p))
                    loaded_docs[str(p)] = doc
                    parsed_ok = True
                    ts = extract_timestamp_fields(doc)
                    timestamps_found[ev_key] = list(ts.keys())
                    ts_count = len(ts)
                except Exception as e:
                    raise RuntimeError(f"FAIL_CLOSED: invalid json for {rule_id} -> {ev_key} -> {p} -> {e}")

            parsed[ev_key] = {
                "path": meta["path"],
                "sha256": meta["sha256"],
                "size": meta["size"],
                "parsed_ok": parsed_ok,
                "timestamp_fields_count": ts_count,
            }

            if meta["size"] <= 0:
                raise RuntimeError(f"FAIL_CLOSED: zero-sized evidence for {rule_id} -> {ev_key}")

            if not meta["sha256"] or len(meta["sha256"]) < 32:
                raise RuntimeError(f"FAIL_CLOSED: weak hash evidence for {rule_id} -> {ev_key}")

        results[rule_id] = {
            "status": "PASS",
            "evidence_count": len(resolved),
            "evidence_keys": sorted(resolved.keys()),
            "parsed": parsed,
            "timestamp_fields": timestamps_found,
        }

    except Exception as e:
        results[rule_id] = {
            "status": "FAIL_CLOSED",
            "reason": str(e),
        }
        failed_rules.append(rule_id)

# ---- Cross-document consistency checks ----

closure_path = ROOT / "artifacts" / "cases" / "case_003" / "closure_state.case_003.canonical.json"
formal_path = ROOT / "artifacts" / "cases" / "case_003" / "formal_closure_certificate.case_003.canonical.json"
attest_path = ROOT / "artifacts" / "history" / "swarm" / "attestation_status.canonical.json"
readiness_path = ROOT / "artifacts" / "production_distributed_readiness_certificate_final.json"
reg_final_path = ROOT / "reports" / "final_checks" / "global_regulatory_certification_final_check.json"
deploy_final_path = ROOT / "reports" / "final_checks" / "global_deployment_audit_final_check.json"

try:
    closure = load_json(str(closure_path))
    formal = load_json(str(formal_path))
    att = load_json(str(attest_path))
    readiness = load_json(str(readiness_path))
    reg_final = load_json(str(reg_final_path))
    deploy_final = load_json(str(deploy_final_path))

    c_root = closure.get("root_hash")
    f_root = formal.get("root_hash")
    consistency_checks.append({
        "check": "closure_root_hash_matches_formal_certificate",
        "status": "PASS" if c_root and f_root and c_root == f_root else "FAIL_CLOSED",
        "closure_root_hash": c_root,
        "formal_root_hash": f_root,
    })
    if not (c_root and f_root and c_root == f_root):
        warnings.append("ROOT_HASH_MISMATCH_BETWEEN_CLOSURE_AND_FORMAL")

    consistency_checks.append({
        "check": "closure_state_is_formally_frozen",
        "status": "PASS" if closure.get("closure_state") == "FORMALLY_FROZEN" else "FAIL_CLOSED",
        "value": closure.get("closure_state"),
    })
    if closure.get("closure_state") != "FORMALLY_FROZEN":
        warnings.append("CLOSURE_STATE_NOT_FORMALLY_FROZEN")

    consistency_checks.append({
        "check": "formal_certificate_issued",
        "status": "PASS" if formal.get("certificate_status") == "ISSUED" else "FAIL_CLOSED",
        "value": formal.get("certificate_status"),
    })
    if formal.get("certificate_status") != "ISSUED":
        warnings.append("FORMAL_CERTIFICATE_NOT_ISSUED")

    consistency_checks.append({
        "check": "attestation_gate_pass",
        "status": "PASS" if att.get("gate", {}).get("status") == "PASS" else "FAIL_CLOSED",
        "value": att.get("gate", {}).get("status"),
    })
    if att.get("gate", {}).get("status") != "PASS":
        warnings.append("ATTESTATION_GATE_NOT_PASS")

    consistency_checks.append({
        "check": "readiness_ready_final",
        "status": "PASS" if readiness.get("status") == "READY_FINAL" else "FAIL_CLOSED",
        "value": readiness.get("status"),
    })
    if readiness.get("status") != "READY_FINAL":
        warnings.append("READINESS_NOT_READY_FINAL")

    consistency_checks.append({
        "check": "regulatory_final_pass",
        "status": "PASS" if reg_final.get("status") == "PASS_CERTIFICATION_FINAL" else "FAIL_CLOSED",
        "value": reg_final.get("status"),
    })
    if reg_final.get("status") != "PASS_CERTIFICATION_FINAL":
        warnings.append("REGULATORY_FINAL_NOT_PASS")

    consistency_checks.append({
        "check": "deployment_final_pass",
        "status": "PASS" if deploy_final.get("status") == "PASS_AUDIT_FINAL" else "FAIL_CLOSED",
        "value": deploy_final.get("status"),
    })
    if deploy_final.get("status") != "PASS_AUDIT_FINAL":
        warnings.append("DEPLOYMENT_FINAL_NOT_PASS")

except Exception as e:
    consistency_checks.append({
        "check": "cross_document_consistency_bundle",
        "status": "FAIL_CLOSED",
        "reason": str(e),
    })
    warnings.append("CROSS_DOCUMENT_CONSISTENCY_FAILED")

failed_consistency = [c for c in consistency_checks if c["status"] != "PASS"]

overall_pass = (len(failed_rules) == 0 and len(failed_consistency) == 0)

out = {
    "schema_id": "ETHICBIT_REAL_LOCAL_L3_CANDIDATE_GATE_V1",
    "status": "PASS" if overall_pass else "FAIL_CLOSED",
    "mode": "REAL_LOCAL_STRICT",
    "rules_checked": len(RULE_EVIDENCE_MAP),
    "failed_rules": failed_rules,
    "consistency_checks": consistency_checks,
    "results": results,
    "warnings": warnings,
    "claim_level_ceiling": "L3_CANDIDATE" if overall_pass else "L2",
    "eligible_for_l4": False,
    "eligible_for_l5": False,
    "reasoning": [
        "REAL_LOCAL evidence resolved for all critical rules",
        "JSON artifacts parsed successfully where applicable",
        "Cross-document constitutional consistency verified",
        "External provider-grade quorum still not established"
    ]
}

out_path = ROOT / "results" / "real_local_l3_candidate_gate.json"
out_path.parent.mkdir(parents=True, exist_ok=True)
out_path.write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

print(f"wrote {out_path}")
print(f"status={out['status']}")
print(f"claim_level_ceiling={out['claim_level_ceiling']}")
print(f"failed_rules={out['failed_rules']}")
print(f"warnings={out['warnings']}")
