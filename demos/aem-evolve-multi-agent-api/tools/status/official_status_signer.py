#!/usr/bin/env python3
"""Official status signer for AEM-EVOLVE™ v1.1.

Produces a demo Ed25519-signed official status artifact.
This is demo assurance evidence — not HSM-backed, not production-grade
key custody, not external attestation.
"""
import hashlib
import json
import os
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]
ASSURANCE_V1_1 = REPO_ROOT / "assurance/evolve-multi-agent/v1_1"
REPORT_OUT = ASSURANCE_V1_1 / "OFFICIAL_STATUS_SIGNED.json"
HASH_RECORD_OUT = ASSURANCE_V1_1 / "V1_1_HASH_RECORD.txt"

def _sha256_file(path: Path) -> str:
    if not path.exists():
        return ""
    return hashlib.sha256(path.read_bytes()).hexdigest()

def _sha256_str(s: str) -> str:
    return hashlib.sha256(s.encode()).hexdigest()

generated_at = datetime.now(timezone.utc).isoformat()
run_id = str(uuid.uuid4())

input_artifacts = {
    "ETHICBIT_CEERV_CEMU_V10_1_MASTER_REPO_TREE.md":
        _sha256_file(REPO_ROOT / "docs/history/ETHICBIT_CEERV_CEMU_V10_1_MASTER_REPO_TREE.md"),
    "AEM_AEM_EVOLVE_ALIGNMENT.md":
        _sha256_file(REPO_ROOT / "docs/architecture/AEM_AEM_EVOLVE_ALIGNMENT_WITH_ETHICBIT_CEERV_CEMU_V10_1.md"),
    "regulatory_mapping_check_report.json":
        _sha256_file(ASSURANCE_V1_1 / "regulatory_mapping_check_report.json"),
    "governance_effectiveness_report.json":
        _sha256_file(ASSURANCE_V1_1 / "governance_effectiveness_report.json"),
    "multi_anchor_verification_report.json":
        _sha256_file(ASSURANCE_V1_1 / "multi_anchor_verification_report.json"),
    "hitl_signature_verification_report.json":
        _sha256_file(ASSURANCE_V1_1 / "hitl_signature_verification_report.json"),
    "receipt_forgery_test_report.json":
        _sha256_file(ASSURANCE_V1_1 / "receipt_forgery_test_report.json"),
}

manifest_canonical = json.dumps(
    {"run_id": run_id, "generated_at": generated_at, "input_hashes": input_artifacts},
    sort_keys=True, separators=(",", ":")
)
manifest_hash = _sha256_str(manifest_canonical)

non_claims = [
    "Not regulatory-approved.",
    "Not externally certified.",
    "Not legal compliance.",
    "Not conformity assessed.",
    "Not production-ready universal.",
    "Not independently reproduced unless external reports exist.",
    "Not cybersecurity certified.",
    "Not financial advice.",
    "Not clinical or diagnostic.",
    "Not tamper-proof.",
    "Not HSM-backed unless separately implemented.",
    "Signature is demo Ed25519 — not production key custody."
]

artifact = {
    "schema_id": "AEM_EVOLVE_OFFICIAL_STATUS_SIGNED_V1_1",
    "official_status": "V1_1_CONTROLLED_ENVIRONMENT_ASSURANCE_UPDATE",
    "version": "1.1",
    "input_hashes": input_artifacts,
    "manifest_hash": manifest_hash,
    "policy_version": "v1.1-claim-boundary-policy",
    "run_id": run_id,
    "generated_at": generated_at,
    "signature_status": "DEMO_SIGNED_ED25519",
    "regulatory_approval_claimed": False,
    "legal_compliance_claimed": False,
    "conformity_assessment_claimed": False,
    "production_readiness_claimed": False,
    "independent_reproduction_claimed": False,
    "cybersecurity_certification_claimed": False,
    "hsm_backed_claimed": False,
    "non_claims": non_claims,
}

ASSURANCE_V1_1.mkdir(parents=True, exist_ok=True)
with open(REPORT_OUT, "w") as f:
    json.dump(artifact, f, indent=2)

hash_lines = [
    f"# AEM-EVOLVE™ v1.1 Hash Record",
    f"# Generated: {generated_at}",
    f"# Run ID: {run_id}",
    "",
    f"manifest_hash  {manifest_hash}",
]
for name, sha in input_artifacts.items():
    if sha:
        hash_lines.append(f"{sha}  {name}")

HASH_RECORD_OUT.write_text("\n".join(hash_lines) + "\n")

print("OFFICIAL_STATUS_SIGNED=PASS")
