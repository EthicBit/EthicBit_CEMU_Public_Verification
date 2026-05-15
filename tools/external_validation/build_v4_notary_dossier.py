#!/usr/bin/env python3
"""Build a scoped AEM-EVOLVE v4.0 Notary Dossier hash record.

This scaffold packages existing dossier files into a hash-verifiable record.
It never elevates status to EXTERNAL_VALIDATION_PASS.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DOSSIER_DIR = ROOT / "assurance/external-validation/v4_0/notary_dossier"
DEFAULT_OUTPUT = DEFAULT_DOSSIER_DIR / "DOSSIER_HASH_RECORD.txt"

REQUIRED_FILES = [
    "README.md",
    "DOSSIER_MANIFEST.json",
    "HUMAN_ATTESTATION_TEMPLATE.md",
    "NON_CLAIMS.md",
]

DISALLOWED_STATUS = "EXTERNAL_VALIDATION_PASS"
ALLOWED_BUILD_STATUSES = {
    "DOSSIER_STRUCTURE_DEFINED",
    "DOSSIER_BUILT",
    "DOSSIER_VERIFIED",
    "DOSSIER_INCOMPLETE",
    "DOSSIER_FAIL_CLOSED",
    "HUMAN_ATTESTATION_PENDING",
}

FALSE_CLAIM_FIELDS = [
    "external_validation_pass_claimed",
    "third_party_reproduction_completed",
    "external_security_review_completed",
    "external_claim_review_completed",
]

FALSE_NON_CLAIMS = [
    "completed_notary_dossier",
    "completed_human_attestation",
    "completed_third_party_reproduction",
    "completed_external_security_review",
    "completed_external_claim_review",
    "external_certification",
    "regulatory_approval",
    "cybersecurity_certification",
    "financial_advice",
    "clinical_or_diagnostic_readiness",
    "universal_production_readiness",
    "legal_compliance",
    "external_validation_pass",
]


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_json_bytes(obj: Any) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def sha256_canonical_json(path: Path) -> str:
    return hashlib.sha256(canonical_json_bytes(json.loads(path.read_text(encoding="utf-8")))).hexdigest()


def load_manifest(dossier_dir: Path) -> dict[str, Any]:
    manifest_path = dossier_dir / "DOSSIER_MANIFEST.json"
    if not manifest_path.exists():
        raise ValueError(f"missing required manifest: {manifest_path}")
    return json.loads(manifest_path.read_text(encoding="utf-8"))


def validate_claim_boundary(manifest: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    status = manifest.get("status")
    if status == DISALLOWED_STATUS:
        errors.append("manifest status must not be EXTERNAL_VALIDATION_PASS")
    if status not in ALLOWED_BUILD_STATUSES:
        errors.append(f"manifest status is not in allowed scaffold statuses: {status!r}")

    for field in FALSE_CLAIM_FIELDS:
        if manifest.get(field) is not False:
            errors.append(f"{field} must be false")

    claim_boundary = manifest.get("claim_boundary", {})
    if claim_boundary.get("automated_pipeline_may_claim_external_validation_pass") is not False:
        errors.append("automated pipeline must not claim external validation pass")
    if claim_boundary.get("human_attestation_required_for_external_validation_elevation") is not True:
        errors.append("human attestation must be required for external-validation elevation")
    if claim_boundary.get("non_claims_required") is not True:
        errors.append("non-claims must be required")

    non_claims = manifest.get("non_claims", {})
    for field in FALSE_NON_CLAIMS:
        if non_claims.get(field) is not False:
            errors.append(f"non_claims.{field} must be false")

    return errors


def existing_dossier_files(dossier_dir: Path, output_path: Path) -> list[Path]:
    files: list[Path] = []
    for path in sorted(dossier_dir.iterdir()):
        if path.is_file() and path.resolve() != output_path.resolve():
            files.append(path)
    return files


def build_hash_record(dossier_dir: Path, output_path: Path) -> tuple[str, str]:
    missing = [name for name in REQUIRED_FILES if not (dossier_dir / name).exists()]
    manifest = load_manifest(dossier_dir)
    boundary_errors = validate_claim_boundary(manifest)
    if boundary_errors:
        lines = "\n".join(f"- {err}" for err in boundary_errors)
        raise ValueError(f"claim boundary validation failed:\n{lines}")

    status = "DOSSIER_BUILT" if not missing else "DOSSIER_INCOMPLETE"
    files = existing_dossier_files(dossier_dir, output_path)
    manifest_path = dossier_dir / "DOSSIER_MANIFEST.json"
    generated_utc = datetime.now(timezone.utc).isoformat()

    lines = [
        "AEM_EVOLVE_V4_0_NOTARY_DOSSIER_HASH_RECORD",
        f"generated_utc={generated_utc}",
        f"status={status}",
        "human_attestation_status=HUMAN_ATTESTATION_PENDING",
        "external_validation_pass_claimed=false",
        "third_party_reproduction_completed=false",
        "external_security_review_completed=false",
        "external_claim_review_completed=false",
        f"dossier_dir={dossier_dir.relative_to(ROOT)}",
        f"required_files_present={str(not missing).lower()}",
    ]
    if missing:
        lines.append("missing_required_files=" + ",".join(missing))
    lines.extend(
        [
            f"manifest_file_sha256={sha256_file(manifest_path)}",
            f"manifest_canonical_sha256={sha256_canonical_json(manifest_path)}",
            "",
            "files:",
        ]
    )

    for path in files:
        rel = path.relative_to(ROOT)
        lines.append(f"{sha256_file(path)}  {rel}")

    record = "\n".join(lines) + "\n"
    return status, record


def main() -> int:
    parser = argparse.ArgumentParser(description="Build AEM-EVOLVE v4.0 Notary Dossier hash record")
    parser.add_argument("--dossier-dir", type=Path, default=DEFAULT_DOSSIER_DIR)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--dry-run", action="store_true", help="Print the hash record without writing it")
    args = parser.parse_args()

    dossier_dir = args.dossier_dir.resolve()
    output_path = args.output.resolve()

    try:
        status, record = build_hash_record(dossier_dir, output_path)
    except Exception as exc:
        print("NOTARY_DOSSIER_BUILD_STATUS=DOSSIER_FAIL_CLOSED")
        print("external_validation_pass_claimed=false")
        print(f"error={exc}")
        return 1

    if args.dry_run:
        print(record, end="")
    else:
        output_path.write_text(record, encoding="utf-8")
        print(f"hash_record_written={output_path}")

    print(f"NOTARY_DOSSIER_BUILD_STATUS={status}")
    print("human_attestation_status=HUMAN_ATTESTATION_PENDING")
    print("external_validation_pass_claimed=false")
    return 0 if status == "DOSSIER_BUILT" else 1


if __name__ == "__main__":
    sys.exit(main())
