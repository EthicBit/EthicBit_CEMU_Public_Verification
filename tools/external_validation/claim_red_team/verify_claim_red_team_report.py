#!/usr/bin/env python3
"""Verify AEM-EVOLVE v4.0 claim-boundary red-team report."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
DEFAULT_REPORT = ROOT / "assurance/external-validation/v4_0/claim_red_team/CLAIM_BOUNDARY_RED_TEAM_REPORT.json"
DEFAULT_CASES = ROOT / "tools/external_validation/claim_red_team/claim_red_team_cases.json"

REQUIRED_CASE_IDS = {
    "regulatory_approval_claim",
    "production_ready_claim",
    "cybersecurity_certified_claim",
    "financial_advice_claim",
    "clinical_diagnostic_claim",
    "tamper_proof_claim",
    "universal_public_anchor_claim",
    "full_system_sub_15ms_claim",
    "third_party_reproduced_claim",
    "external_certified_claim",
}


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def verify(report: dict[str, Any], cases: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    expected_count = len(cases.get("cases", []))
    report_cases = report.get("cases", [])

    if report.get("claim_boundary_red_team") != "PASS":
        errors.append("claim_boundary_red_team must be PASS")
    if report.get("status") != "CLAIM_BOUNDARY_RED_TEAM_PASS":
        errors.append("status must be CLAIM_BOUNDARY_RED_TEAM_PASS")
    if report.get("overclaims_attempted") != expected_count:
        errors.append("overclaims_attempted must equal case count")
    if report.get("overclaims_blocked") != expected_count:
        errors.append("overclaims_blocked must equal case count")
    if report.get("overclaims_failed_to_block") != 0:
        errors.append("overclaims_failed_to_block must be 0")
    if report.get("block_rate_percent") != 100.0:
        errors.append("block_rate_percent must be 100.0")
    if report.get("external_claim_review_completed") is not False:
        errors.append("external_claim_review_completed must be false")
    if report.get("external_validation_pass_claimed") is not False:
        errors.append("external_validation_pass_claimed must be false")
    if report.get("human_attestation_status") != "HUMAN_ATTESTATION_PENDING":
        errors.append("human_attestation_status must remain HUMAN_ATTESTATION_PENDING")

    attempted_ids = {case.get("attempted_claim_id") for case in report_cases}
    missing = sorted(REQUIRED_CASE_IDS - attempted_ids)
    if missing:
        errors.append("missing required red-team claim cases: " + ",".join(missing))

    for case in report_cases:
        if case.get("decision") != "BLOCKED":
            errors.append(f"case {case.get('case_id')} did not block attempted claim")
        if not case.get("permitted_alternative"):
            errors.append(f"case {case.get('case_id')} missing permitted alternative")

    boundary = report.get("claim_boundary", {})
    if boundary.get("human_review_required_for_external_claim_review_completion") is not True:
        errors.append("human review must be required for external claim review completion")
    if boundary.get("external_claim_review_completed") is not False:
        errors.append("boundary.external_claim_review_completed must be false")
    if boundary.get("external_validation_pass_claimed") is not False:
        errors.append("boundary.external_validation_pass_claimed must be false")

    non_claims = report.get("non_claims", {})
    for field in (
        "completed_external_claim_review",
        "completed_external_validation",
        "external_certification",
        "regulatory_approval",
        "cybersecurity_certification",
        "financial_advice",
        "clinical_or_diagnostic_readiness",
        "universal_production_readiness",
        "third_party_reproduction_completed",
    ):
        if non_claims.get(field) is not False:
            errors.append(f"non_claims.{field} must be false")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify AEM-EVOLVE v4.0 claim-boundary red-team report")
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--cases", type=Path, default=DEFAULT_CASES)
    args = parser.parse_args()

    report = load_json(args.report.resolve())
    cases = load_json(args.cases.resolve())
    errors = verify(report, cases)
    if errors:
        print("CLAIM_BOUNDARY_RED_TEAM_VERIFICATION=FAIL_CLOSED")
        print("external_claim_review_completed=false")
        for error in errors:
            print(f"error={error}")
        return 1

    print("CLAIM_BOUNDARY_RED_TEAM_VERIFICATION=PASS")
    print(f"overclaims_attempted={report['overclaims_attempted']}")
    print(f"overclaims_blocked={report['overclaims_blocked']}")
    print("block_rate=100%")
    print("external_claim_review_completed=false")
    print("HUMAN_ATTESTATION_PENDING=true")
    return 0


if __name__ == "__main__":
    sys.exit(main())
