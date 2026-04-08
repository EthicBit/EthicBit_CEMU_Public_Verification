#!/usr/bin/env python3
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

REQUIRED_FILES = [
    "cemu/builders/runtime_guard.py",
    "cemu/builders/runtime_guard_l4_policy.json",
    "cemu/builders/runtime_guard_l4_checklist.json",
    "assurance/in-toto/root.layout",
    "assurance/slsa/provenance.json",
    "assurance/slsa/level4-policy.json",
    "assurance/slsa/subject-index.json",
    "assurance/sigstore/policy.json",
    "regulatory/policies/regulatory_policy_baseline.json",
]

def main():
    results = []
    all_ok = True

    for rel in REQUIRED_FILES:
        exists = (ROOT / rel).exists()
        results.append({"path": rel, "exists": exists})
        if not exists:
            all_ok = False

    status = "ALLOW_BASELINE" if all_ok else "BLOCK_BASELINE"

    out = {
        "check_id": "RUNTIMEGUARD_L4_BASELINE_CHECK",
        "status": status,
        "results": results,
    }

    out_path = ROOT / "reports/baseline_checks/runtimeguard_l4_baseline_check.json"
    out_path.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(json.dumps(out, indent=2))

if __name__ == "__main__":
    main()
