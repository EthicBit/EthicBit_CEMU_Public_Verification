#!/usr/bin/env python3
"""Verify AEM-EVOLVE v4.0 automated reproduction support artifacts."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Dict

ROOT = Path(__file__).resolve().parents[3]
DEFAULT_DIR = ROOT / "assurance/external-validation/v4_0/automated_reproduction"


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
    parser.add_argument("--artifact-dir", default=str(DEFAULT_DIR), help="Directory containing automated reproduction artifacts")
    args = parser.parse_args()

    artifact_dir = Path(args.artifact_dir).resolve()
    report_path = artifact_dir / "AUTOMATED_REPRODUCTION_REPORT.json"
    log_path = artifact_dir / "AUTOMATED_REPRODUCTION_LOG.txt"
    hash_record_path = artifact_dir / "AUTOMATED_REPRODUCTION_HASH_RECORD.txt"

    report = json.loads(report_path.read_text(encoding="utf-8"))
    log_text = log_path.read_text(encoding="utf-8")
    hashes = parse_hash_record(hash_record_path)

    require(report.get("automated_reproduction_support") == "PASS", "automated reproduction support must be PASS")
    require(report.get("pre_report_full_stack_verification") == "PASS", "full-stack support summary must be PASS")
    require(report.get("ai_me_v3_1") == "PASS", "AI-ME v3.1 support must be PASS")
    require(report.get("fast_path_v1_0") == "PASS", "Fast Path v1.0 support must be PASS")
    require(report.get("claim_boundary_red_team") == "PASS", "claim red-team support must be PASS")
    require(report.get("notary_dossier_human_attestation") == "HUMAN_ATTESTATION_PENDING", "human attestation must remain pending")
    require(all(item.get("passed") for item in report.get("checks", [])), "all report checks must pass")

    non_claims = report.get("non_claims", {})
    require(non_claims.get("third_party_reproduction_completed") is False, "must not claim third-party reproduction completion")
    require(non_claims.get("completed_external_validation") is False, "must not claim completed external validation")
    require(non_claims.get("external_certification") is False, "must not claim external certification")
    require(report.get("claim_boundary", {}).get("automated_pipeline_may_claim_third_party_reproduction") is False, "pipeline must not claim third-party reproduction")
    require(report.get("claim_boundary", {}).get("automated_pipeline_may_claim_external_validation_pass") is False, "pipeline must not claim external validation pass")

    required_log_lines = [
        "AUTOMATED_REPRODUCTION_SUPPORT=PASS",
        "PRE_REPORT_FULL_STACK_VERIFICATION=PASS",
        "AI_ME_V3_1=PASS",
        "FAST_PATH_V1_0=PASS",
        "third_party_reproduction_completed=false",
        "external_validation_pass_claimed=false",
        "HUMAN_ATTESTATION_PENDING=true",
    ]
    for line in required_log_lines:
        require(line in log_text, f"missing log line: {line}")

    require(hashes.get("AUTOMATED_REPRODUCTION_REPORT.json") == sha256_file(report_path), "report hash mismatch")
    require(hashes.get("AUTOMATED_REPRODUCTION_LOG.txt") == sha256_file(log_path), "log hash mismatch")
    require("third_party_reproduction_completed=true" not in log_text, "forbidden external reproduction completion claim in log")

    print("AUTOMATED_REPRODUCTION_SUPPORT_VERIFICATION=PASS")
    print("AUTOMATED_REPRODUCTION_SUPPORT=PASS")
    print("PRE_REPORT_FULL_STACK_VERIFICATION=PASS")
    print("AI_ME_V3_1=PASS")
    print("FAST_PATH_V1_0=PASS")
    print("third_party_reproduction_completed=false")
    print("HUMAN_ATTESTATION_PENDING=true")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:
        print(f"AUTOMATED_REPRODUCTION_SUPPORT_VERIFICATION=FAIL: {exc}", file=sys.stderr)
        sys.exit(1)
