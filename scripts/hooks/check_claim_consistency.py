#!/usr/bin/env python3
"""Pre-commit hook: verify claim boundary consistency across assurance artifacts.

Checks that:
  1. attestation-index.json status is consistent with individual statement statuses.
  2. level4-policy.json full_l4_claim_allowed is False when in-toto is not externally witnessed.
  3. No staged file elevates human_attestation_status to HUMAN_ATTESTED without
     external_claim_review_completed = true.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


def check_attestation_index() -> list[str]:
    path = REPO_ROOT / "assurance/in-toto/attestation-index.json"
    if not path.exists():
        return []
    data = json.loads(path.read_text())
    errors: list[str] = []
    index_status = data.get("status", "")
    for attestation in data.get("attestations", []):
        step_status = attestation.get("status", "")
        if index_status == "VERIFIED" and step_status != "VERIFIED":
            errors.append(
                f"attestation-index.json claims VERIFIED but step '{attestation['step']}' is {step_status}"
            )
    return errors


def check_slsa_policy() -> list[str]:
    path = REPO_ROOT / "assurance/slsa/l4/level4-policy.json"
    if not path.exists():
        return []
    data = json.loads(path.read_text())
    errors: list[str] = []
    enforcement = data.get("enforcement", {})

    in_toto_status = enforcement.get("in_toto_signing_status", "")
    full_l4 = enforcement.get("full_l4_claim_allowed", False)

    if full_l4 and "EXTERNALLY_WITNESSED" not in in_toto_status:
        errors.append(
            "level4-policy.json: full_l4_claim_allowed=true but in-toto chain is not EXTERNALLY_WITNESSED"
        )
    return errors


def check_no_automated_human_attestation_elevation() -> list[str]:
    """Scan staged claim boundary files for accidental HUMAN_ATTESTED elevation."""
    errors: list[str] = []
    targets = [
        REPO_ROOT / "tools/external_validation/claim_red_team/claim_boundary_regression_cases.json",
        REPO_ROOT / "assurance/in-toto/attestation-index.json",
    ]
    for path in targets:
        if not path.exists():
            continue
        data = json.loads(path.read_text())
        status = data.get("human_attestation_status", "")
        ext_review = data.get("external_claim_review_completed", False)
        if status == "HUMAN_ATTESTED" and not ext_review:
            errors.append(
                f"{path.name}: human_attestation_status=HUMAN_ATTESTED but external_claim_review_completed=false — requires out-of-band authorization"
            )
    return errors


def main() -> int:
    errors: list[str] = []
    errors.extend(check_attestation_index())
    errors.extend(check_slsa_policy())
    errors.extend(check_no_automated_human_attestation_elevation())

    if errors:
        print("Claim consistency check FAILED:")
        for e in errors:
            print(f"  {e}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
