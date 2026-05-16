#!/usr/bin/env python3
"""Verify AEM-EVOLVE v4.0 automated security-review support artifacts."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Dict

ROOT = Path(__file__).resolve().parents[3]
DEFAULT_DIR = ROOT / "assurance/external-validation/v4_0/security_review"
SUMMARY_NAME = "AUTOMATED_SECURITY_REVIEW_SUMMARY.json"
LOG_NAME = "AUTOMATED_SECURITY_REVIEW_LOG.txt"
HASH_RECORD_NAME = "SECURITY_SCAN_HASH_RECORD.txt"


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def parse_hash_record(path: Path) -> Dict[str, str]:
    hashes: Dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        parts = line.split()
        if len(parts) >= 2 and len(parts[0]) == 64:
            hashes[parts[1]] = parts[0]
    return hashes


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifact-dir", default=str(DEFAULT_DIR), help="Directory containing security review support artifacts")
    args = parser.parse_args()

    artifact_dir = Path(args.artifact_dir).resolve()
    summary_path = artifact_dir / SUMMARY_NAME
    log_path = artifact_dir / LOG_NAME
    hash_record_path = artifact_dir / HASH_RECORD_NAME

    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    log_text = log_path.read_text(encoding="utf-8")
    hashes = parse_hash_record(hash_record_path)

    require(summary.get("automated_security_review_support") == "PASS", "automated security review support must be PASS")
    require(summary.get("critical_findings") == 0, "critical findings must be zero")
    require(summary.get("secret_findings") == 0, "secret findings must be zero")
    require(summary.get("dependency_inventory_status") == "GENERATED", "dependency inventory must be generated")
    require(summary.get("dependency_manifest_count", 0) > 0, "dependency manifest inventory must not be empty")
    require(all(item.get("passed") for item in summary.get("checks", [])), "all summary checks must pass")

    non_claims = summary.get("non_claims", {})
    require(non_claims.get("completed_external_security_review") is False, "must not claim completed external security review")
    require(non_claims.get("cybersecurity_certification") is False, "must not claim cybersecurity certification")
    require(non_claims.get("absence_of_all_vulnerabilities") is False, "must not claim absence of all vulnerabilities")
    require(summary.get("claim_boundary", {}).get("automated_pipeline_may_claim_external_security_review_completed") is False, "pipeline must not claim external security review completion")
    require(summary.get("claim_boundary", {}).get("automated_pipeline_may_claim_cybersecurity_certification") is False, "pipeline must not claim cybersecurity certification")

    required_log_lines = [
        "AUTOMATED_SECURITY_REVIEW_SUPPORT=PASS",
        "critical_findings=0",
        "secret_findings=0",
        "external_security_review_completed=false",
        "cybersecurity_certification=false",
        "absence_of_all_vulnerabilities=false",
        "HUMAN_ATTESTATION_PENDING=true",
    ]
    for line in required_log_lines:
        require(line in log_text, f"missing log line: {line}")

    require(hashes.get(SUMMARY_NAME) == sha256_file(summary_path), "summary hash mismatch")
    require(hashes.get(LOG_NAME) == sha256_file(log_path), "log hash mismatch")
    forbidden = [
        "external_security_review_completed=true",
        "cybersecurity_certification=true",
        "absence_of_all_vulnerabilities=true",
    ]
    for marker in forbidden:
        require(marker not in log_text, f"forbidden claim in log: {marker}")

    print("AUTOMATED_SECURITY_REVIEW_SUPPORT_VERIFICATION=PASS")
    print("AUTOMATED_SECURITY_REVIEW_SUPPORT=PASS")
    print("critical_findings=0")
    print("secret_findings=0")
    print("external_security_review_completed=false")
    print("cybersecurity_certification=false")
    print("HUMAN_ATTESTATION_PENDING=true")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:
        print(f"AUTOMATED_SECURITY_REVIEW_SUPPORT_VERIFICATION=FAIL: {exc}", file=sys.stderr)
        sys.exit(1)
