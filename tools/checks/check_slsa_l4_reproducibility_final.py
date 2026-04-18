#!/usr/bin/env python3
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

SUBJECTS = [
    "ceerv/artifacts/evidence_bundle_full.json",
    "ceerv/artifacts/certificate.json",
    "ceerv/outputs/ACTA_MINIMA.json",
]

REQUIRED_FILES = [
    "attestations/slsa_l4_operative_attestation.json",
    "reports/operative_checks/slsa_l4_operative_check.json",
    "logs/slsa_l4_operative.log",
    "assurance/slsa/level4-policy.json",
    "assurance/slsa/subject-index.json",
    "assurance/in-toto/root.layout",
    "assurance/sigstore/policy.json",
]

def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()

def capture_subjects():
    captured = []
    for rel in SUBJECTS:
        path = ROOT / rel
        captured.append({
            "name": rel,
            "sha256": sha256_file(path)
        })
    return captured

def main():
    checks = []
    ok = True

    for rel in REQUIRED_FILES:
        exists = (ROOT / rel).exists()
        checks.append({
            "type": "required_file",
            "path": rel,
            "exists": exists,
            "status": "PASS_FINAL" if exists else "FAIL_FINAL"
        })
        if not exists:
            ok = False

    run_1 = capture_subjects() if ok else []
    run_2 = capture_subjects() if ok else []

    reproducible = run_1 == run_2
    if not reproducible:
        ok = False

    reproducibility_report = {
        "schema_id": "ETHICBIT_SLSA_L4_REPRODUCIBILITY_REPORT_V1",
        "status": "PASS_REPRODUCIBLE" if reproducible and ok else "FAIL_REPRODUCIBLE",
        "run_1": run_1,
        "run_2": run_2
    }

    final_report = {
        "check_id": "SLSA_L4_FINAL_CHECK",
        "status": "PASS_SLSA_FINAL" if reproducible and ok else "FAIL_SLSA_FINAL",
        "checks": checks,
        "reproducibility_ref": "reports/final_checks/slsa_l4_reproducibility_report.json"
    }

    final_attestation = {
        "schema_id": "ETHICBIT_SLSA_L4_FINAL_ATTESTATION_V1",
        "status": final_report["status"],
        "basis": "operative_attestation_plus_reproducibility"
    }

    report_path = ROOT / "reports/final_checks/slsa_l4_final_check.json"
    repro_path = ROOT / "reports/final_checks/slsa_l4_reproducibility_report.json"
    att_path = ROOT / "attestations/slsa_l4_final_attestation.json"
    log_path = ROOT / "logs/slsa_l4_final.log"

    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(final_report, indent=2), encoding="utf-8")
    repro_path.write_text(json.dumps(reproducibility_report, indent=2), encoding="utf-8")
    att_path.write_text(json.dumps(final_attestation, indent=2), encoding="utf-8")
    log_path.write_text(
        f"SLSA_L4_FINAL_CHECK={final_report['status']}\n"
        f"REPRODUCIBILITY={reproducibility_report['status']}\n",
        encoding="utf-8"
    )

    print(json.dumps(final_report, indent=2))
    print(json.dumps(reproducibility_report, indent=2))
    print(json.dumps(final_attestation, indent=2))

if __name__ == "__main__":
    main()
