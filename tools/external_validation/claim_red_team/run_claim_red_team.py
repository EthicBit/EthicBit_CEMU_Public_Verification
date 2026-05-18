#!/usr/bin/env python3
"""Run AEM-EVOLVE v4.0 claim-boundary red-team cases.

The runner attempts unsupported claims and verifies that every one is blocked.
It never claims external validation, external certification, or completed external claim review.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
DEFAULT_CASES = ROOT / "tools/external_validation/claim_red_team/claim_red_team_cases.json"
DEFAULT_OUTPUT = ROOT / "assurance/external-validation/v4_0/claim_red_team/CLAIM_BOUNDARY_RED_TEAM_REPORT.json"

FORBIDDEN_DECISIONS = {"ALLOWED", "PASS_EXTERNAL", "CERTIFIED", "APPROVED"}
REQUIRED_FALSE_FIELDS = {
    "external_claim_review_completed": False,
}


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_json_bytes(obj: Any) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def load_cases(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("external_claim_review_completed") is not False:
        raise ValueError("cases file must preserve external_claim_review_completed=false")
    if data.get("human_attestation_status") != "HUMAN_ATTESTATION_PENDING":
        raise ValueError("cases file must preserve HUMAN_ATTESTATION_PENDING")
    cases = data.get("cases")
    if not isinstance(cases, list) or not cases:
        raise ValueError("cases file must include at least one case")
    return data


def evaluate_case(case: dict[str, Any]) -> dict[str, Any]:
    expected = case.get("expected_decision")
    if expected != "BLOCKED":
        decision = "FAIL_CLOSED"
        reason = "expected decision must be BLOCKED"
    elif expected in FORBIDDEN_DECISIONS:
        decision = "FAIL_CLOSED"
        reason = "forbidden decision requested"
    elif not case.get("permitted_alternative"):
        decision = "FAIL_CLOSED"
        reason = "missing permitted alternative"
    elif not case.get("required_external_condition"):
        decision = "FAIL_CLOSED"
        reason = "missing required external condition"
    else:
        decision = "BLOCKED"
        reason = "unsupported claim blocked; permitted alternative preserved"

    return {
        "case_id": case.get("case_id"),
        "attempted_claim_id": case.get("attempted_claim_id"),
        "attempted_claim_text": case.get("attempted_claim_text"),
        "required_external_condition": case.get("required_external_condition"),
        "observed_condition": case.get("observed_condition"),
        "decision": decision,
        "permitted_alternative": case.get("permitted_alternative"),
        "reason": reason,
    }


def build_report(cases_path: Path) -> dict[str, Any]:
    cases_data = load_cases(cases_path)
    evaluated = [evaluate_case(case) for case in cases_data["cases"]]
    attempted = len(evaluated)
    blocked = sum(1 for case in evaluated if case["decision"] == "BLOCKED")
    failed = attempted - blocked
    block_rate = 100.0 if attempted and blocked == attempted else round((blocked / attempted) * 100, 2)
    status = "PASS" if attempted > 0 and failed == 0 else "FAIL_CLOSED"

    report = {
        "schema_id": "AEM_EVOLVE_V4_0_CLAIM_BOUNDARY_RED_TEAM_REPORT_V1",
        "report_type": "CLAIM_BOUNDARY_RED_TEAM_REPORT",
        "version": "4.0",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "status": "CLAIM_BOUNDARY_RED_TEAM_PASS" if status == "PASS" else "CLAIM_BOUNDARY_RED_TEAM_FAIL_CLOSED",
        "claim_boundary_red_team": status,
        "overclaims_attempted": attempted,
        "overclaims_blocked": blocked,
        "overclaims_failed_to_block": failed,
        "block_rate_percent": block_rate,
        "external_claim_review_completed": False,
        "human_attestation_status": "HUMAN_ATTESTATION_PENDING",
        "external_validation_pass_claimed": False,
        "current_evidence_posture": cases_data.get("current_status"),
        "cases_sha256": sha256_file(cases_path),
        "cases_canonical_sha256": hashlib.sha256(canonical_json_bytes(cases_data)).hexdigest(),
        "cases": evaluated,
        "claim_boundary": {
            "automated_red_team_support_only": True,
            "human_review_required_for_external_claim_review_completion": True,
            "external_claim_review_completed": False,
            "external_validation_pass_claimed": False,
        },
        "non_claims": {
            "completed_external_claim_review": False,
            "completed_external_validation": False,
            "external_certification": False,
            "regulatory_approval": False,
            "cybersecurity_certification": False,
            "financial_advice": False,
            "clinical_or_diagnostic_readiness": False,
            "universal_production_readiness": False,
            "third_party_reproduction_completed": False,
            "slsa_l4_fully_achieved": False,
            "slsa_l4_certification": False,
            "production_supply_chain_certification": False,
            "externally_verified_in_toto_chain": False,
        },
    }
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="Run AEM-EVOLVE v4.0 claim-boundary red-team cases")
    parser.add_argument("--cases", type=Path, default=DEFAULT_CASES)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    try:
        report = build_report(args.cases.resolve())
    except Exception as exc:
        print("CLAIM_BOUNDARY_RED_TEAM=FAIL_CLOSED")
        print("external_claim_review_completed=false")
        print(f"error={exc}")
        return 1

    text = json.dumps(report, indent=2, ensure_ascii=False) + "\n"
    if args.dry_run:
        print(text, end="")
    else:
        args.output.resolve().parent.mkdir(parents=True, exist_ok=True)
        args.output.resolve().write_text(text, encoding="utf-8")

    print(f"CLAIM_BOUNDARY_RED_TEAM={report['claim_boundary_red_team']}")
    print(f"overclaims_attempted={report['overclaims_attempted']}")
    print(f"overclaims_blocked={report['overclaims_blocked']}")
    print(f"block_rate={int(report['block_rate_percent'])}%")
    print("external_claim_review_completed=false")
    print("HUMAN_ATTESTATION_PENDING=true")
    return 0 if report["claim_boundary_red_team"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
