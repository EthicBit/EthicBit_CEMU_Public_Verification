#!/usr/bin/env python3
"""Verify the AEM-EVOLVE v4.0 Notary Dossier scaffold or hash record.

This verifier is intentionally claim-bound. It never emits EXTERNAL_VALIDATION_PASS.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DOSSIER_DIR = ROOT / "assurance/external-validation/v4_0/notary_dossier"
DEFAULT_HASH_RECORD = DEFAULT_DOSSIER_DIR / "DOSSIER_HASH_RECORD.txt"
DEFAULT_SCHEMA = ROOT / "tools/external_validation/notary_dossier_schema.json"

REQUIRED_FILES = [
    "README.md",
    "DOSSIER_MANIFEST.json",
    "HUMAN_ATTESTATION_TEMPLATE.md",
    "NON_CLAIMS.md",
]

REQUIRED_MANIFEST_KEYS = [
    "schema_id",
    "dossier_name",
    "version",
    "status",
    "human_attestation_status",
    "external_validation_pass_claimed",
    "third_party_reproduction_completed",
    "external_security_review_completed",
    "external_claim_review_completed",
    "claim_boundary",
    "non_claims",
]

FORBIDDEN_STATUS = "EXTERNAL_VALIDATION_PASS"
FALSE_FIELDS = [
    "external_validation_pass_claimed",
    "third_party_reproduction_completed",
    "external_security_review_completed",
    "external_claim_review_completed",
]


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def verify_manifest(dossier_dir: Path, schema_path: Path) -> list[str]:
    errors: list[str] = []
    manifest_path = dossier_dir / "DOSSIER_MANIFEST.json"
    if not schema_path.exists():
        errors.append(f"missing schema: {schema_path}")
    else:
        schema = load_json(schema_path)
        status_enum = schema.get("properties", {}).get("status", {}).get("enum", [])
        if FORBIDDEN_STATUS in status_enum:
            errors.append("schema must not allow EXTERNAL_VALIDATION_PASS as an automated status")
    if not manifest_path.exists():
        errors.append(f"missing manifest: {manifest_path}")
        return errors

    manifest = load_json(manifest_path)
    for key in REQUIRED_MANIFEST_KEYS:
        if key not in manifest:
            errors.append(f"manifest missing key: {key}")

    if manifest.get("status") == FORBIDDEN_STATUS:
        errors.append("manifest status must not be EXTERNAL_VALIDATION_PASS")
    if manifest.get("human_attestation_status") != "HUMAN_ATTESTATION_PENDING":
        errors.append("human_attestation_status must remain HUMAN_ATTESTATION_PENDING in this scaffold")
    for field in FALSE_FIELDS:
        if manifest.get(field) is not False:
            errors.append(f"{field} must be false")

    boundary = manifest.get("claim_boundary", {})
    if boundary.get("automated_pipeline_may_claim_external_validation_pass") is not False:
        errors.append("automated pipeline must not claim external validation pass")
    if boundary.get("human_attestation_required_for_external_validation_elevation") is not True:
        errors.append("human attestation must be required")

    non_claims = manifest.get("non_claims", {})
    if non_claims.get("external_validation_pass") is not False:
        errors.append("non_claims.external_validation_pass must be false")
    return errors


def verify_required_files(dossier_dir: Path) -> list[str]:
    return [f"missing required file: {name}" for name in REQUIRED_FILES if not (dossier_dir / name).exists()]


def parse_hash_record(path: Path) -> tuple[list[str], list[tuple[str, Path]]]:
    errors: list[str] = []
    entries: list[tuple[str, Path]] = []
    content = path.read_text(encoding="utf-8")
    if "EXTERNAL_VALIDATION_PASS" in content:
        errors.append("hash record must not contain EXTERNAL_VALIDATION_PASS")
    if "external_validation_pass_claimed=false" not in content:
        errors.append("hash record must preserve external_validation_pass_claimed=false")
    if "human_attestation_status=HUMAN_ATTESTATION_PENDING" not in content:
        errors.append("hash record must preserve HUMAN_ATTESTATION_PENDING")

    in_files = False
    for line in content.splitlines():
        if line == "files:":
            in_files = True
            continue
        if not in_files or not line.strip():
            continue
        match = re.match(r"^([0-9a-f]{64})\s{2}(.+)$", line)
        if not match:
            errors.append(f"invalid hash record line: {line}")
            continue
        entries.append((match.group(1), ROOT / match.group(2)))
    return errors, entries


def verify_hash_record(path: Path) -> list[str]:
    errors, entries = parse_hash_record(path)
    for expected, file_path in entries:
        if not file_path.exists():
            errors.append(f"hash record references missing file: {file_path.relative_to(ROOT)}")
            continue
        observed = sha256_file(file_path)
        if observed != expected:
            errors.append(f"hash mismatch: {file_path.relative_to(ROOT)}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify AEM-EVOLVE v4.0 Notary Dossier")
    parser.add_argument("--dossier-dir", type=Path, default=DEFAULT_DOSSIER_DIR)
    parser.add_argument("--schema", type=Path, default=DEFAULT_SCHEMA)
    parser.add_argument("--hash-record", type=Path, default=DEFAULT_HASH_RECORD)
    parser.add_argument("--structure-only", action="store_true", help="Verify current scaffold without requiring DOSSIER_HASH_RECORD.txt")
    args = parser.parse_args()

    dossier_dir = args.dossier_dir.resolve()
    errors: list[str] = []
    errors.extend(verify_required_files(dossier_dir))
    errors.extend(verify_manifest(dossier_dir, args.schema.resolve()))

    if not args.structure_only:
        hash_record = args.hash_record.resolve()
        if not hash_record.exists():
            errors.append(f"missing hash record: {hash_record}")
        else:
            errors.extend(verify_hash_record(hash_record))

    if errors:
        print("NOTARY_DOSSIER_VERIFICATION_STATUS=DOSSIER_FAIL_CLOSED")
        print("external_validation_pass_claimed=false")
        for error in errors:
            print(f"error={error}")
        return 1

    print("NOTARY_DOSSIER_VERIFICATION_STATUS=DOSSIER_VERIFIED")
    print("human_attestation_status=HUMAN_ATTESTATION_PENDING")
    print("external_validation_pass_claimed=false")
    print("external_validation_pass=false")
    return 0


if __name__ == "__main__":
    sys.exit(main())
