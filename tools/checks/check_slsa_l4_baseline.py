#!/usr/bin/env python3
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

REQUIRED_FILES = [
    "ceerv/artifacts/evidence_bundle_full.json",
    "ceerv/artifacts/certificate.json",
    "ceerv/outputs/ACTA_MINIMA.json",
    "assurance/slsa/level4-policy.json",
    "assurance/slsa/subject-index.json",
    "assurance/in-toto/root.layout",
    "assurance/sigstore/policy.json",
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
        "check_id": "SLSA_L4_BASELINE_CHECK",
        "status": "PASS_BASELINE" if all_ok else "FAIL_BASELINE",
        "results": results,
    }

    out_path = ROOT / "reports/baseline_checks/slsa_l4_baseline_check.json"
    out_path.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(json.dumps(out, indent=2))

if __name__ == "__main__":
    main()
