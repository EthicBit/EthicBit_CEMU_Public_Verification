#!/usr/bin/env python3
import hashlib
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
    "assurance/slsa/l4-operative-checklist.json",
]

SUBJECTS = [
    "ceerv/artifacts/evidence_bundle_full.json",
    "ceerv/artifacts/certificate.json",
    "ceerv/outputs/ACTA_MINIMA.json",
]

def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()

def main():
    results = []
    all_ok = True

    for rel in REQUIRED_FILES:
        exists = (ROOT / rel).exists()
        results.append({"path": rel, "exists": exists})
        if not exists:
            all_ok = False

    subject_digests = []
    if all_ok:
        for rel in SUBJECTS:
            digest = sha256_file(ROOT / rel)
            subject_digests.append({
                "name": rel,
                "sha256": digest
            })

    attestation = {
        "schema_id": "ETHICBIT_SLSA_L4_OPERATIVE_ATTESTATION_V1",
        "status": "OPERATIVE_BASELINE_ATTESTED" if all_ok else "OPERATIVE_BASELINE_INCOMPLETE",
        "subjects": subject_digests
    }

    report = {
        "check_id": "SLSA_L4_OPERATIVE_CHECK",
        "status": "PASS_OPERATIVE_BASELINE" if all_ok else "FAIL_OPERATIVE_BASELINE",
        "results": results,
        "subjects": subject_digests
    }

    att_path = ROOT / "attestations/slsa_l4_operative_attestation.json"
    rep_path = ROOT / "reports/operative_checks/slsa_l4_operative_check.json"
    log_path = ROOT / "logs/slsa_l4_operative.log"

    att_path.write_text(json.dumps(attestation, indent=2), encoding="utf-8")
    rep_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    log_path.write_text(
        f"SLSA_L4_OPERATIVE_CHECK={report['status']}\n"
        + "\n".join(f"{s['name']} {s['sha256']}" for s in subject_digests),
        encoding="utf-8"
    )

    print(json.dumps(report, indent=2))

if __name__ == "__main__":
    main()
