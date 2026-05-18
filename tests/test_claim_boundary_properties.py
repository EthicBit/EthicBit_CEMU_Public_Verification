#!/usr/bin/env python3
"""Property-based tests for the claim-boundary engine using Hypothesis.

Covers five structural invariants and one meta-invariant:
  I-1  Every case with expected_decision=BLOCKED evaluates to BLOCKED.
  I-2  Any case missing permitted_alternative evaluates to FAIL_CLOSED.
  I-3  Any case missing required_external_condition evaluates to FAIL_CLOSED.
  I-4  Any case with expected_decision != BLOCKED evaluates to FAIL_CLOSED.
  I-5  non_claims block: all 13 fields are always False.
  I-M  Injecting a non-BLOCKED case into the corpus → report status FAIL_CLOSED.
"""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path
from typing import Any

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "tools" / "external_validation" / "claim_red_team"))

from run_claim_red_team import (  # noqa: E402  (import after sys.path)
    FORBIDDEN_DECISIONS,
    build_report,
    evaluate_case,
    load_cases,
)

CASES_PATH = REPO_ROOT / "tools/external_validation/claim_red_team/claim_boundary_regression_cases.json"

NON_CLAIM_FIELDS = [
    "completed_external_claim_review",
    "completed_external_validation",
    "external_certification",
    "regulatory_approval",
    "cybersecurity_certification",
    "financial_advice",
    "clinical_or_diagnostic_readiness",
    "universal_production_readiness",
    "third_party_reproduction_completed",
    "slsa_l4_fully_achieved",
    "slsa_l4_certification",
    "production_supply_chain_certification",
    "externally_verified_in_toto_chain",
]

_nonempty_text = st.text(min_size=1, max_size=200).filter(lambda s: s.strip())


def _base_valid_case() -> st.SearchStrategy[dict[str, Any]]:
    return st.fixed_dictionaries(
        {
            "case_id": st.text(min_size=1, max_size=50),
            "attempted_claim_id": st.text(min_size=1, max_size=100),
            "attempted_claim_text": _nonempty_text,
            "required_external_condition": _nonempty_text,
            "observed_condition": _nonempty_text,
            "expected_decision": st.just("BLOCKED"),
            "permitted_alternative": _nonempty_text,
        }
    )


# ---------------------------------------------------------------------------
# I-1: expected_decision=BLOCKED → result is BLOCKED
# ---------------------------------------------------------------------------

@given(_base_valid_case())
@settings(max_examples=500, suppress_health_check=[HealthCheck.too_slow])
def test_i1_blocked_case_always_evaluates_blocked(case: dict[str, Any]) -> None:
    result = evaluate_case(case)
    assert result["decision"] == "BLOCKED", (
        f"Expected BLOCKED for case with expected_decision=BLOCKED, got {result['decision']}: {result['reason']}"
    )


# ---------------------------------------------------------------------------
# I-2: missing permitted_alternative → FAIL_CLOSED
# ---------------------------------------------------------------------------

@given(
    _base_valid_case().flatmap(
        lambda c: st.fixed_dictionaries(
            {**{k: st.just(v) for k, v in c.items()}, "permitted_alternative": st.just("")}
        )
    )
)
@settings(max_examples=500, suppress_health_check=[HealthCheck.too_slow])
def test_i2_missing_permitted_alternative_is_fail_closed(case: dict[str, Any]) -> None:
    result = evaluate_case(case)
    assert result["decision"] == "FAIL_CLOSED", (
        f"Expected FAIL_CLOSED when permitted_alternative is empty, got {result['decision']}"
    )


# ---------------------------------------------------------------------------
# I-3: missing required_external_condition → FAIL_CLOSED
# ---------------------------------------------------------------------------

@given(
    _base_valid_case().flatmap(
        lambda c: st.fixed_dictionaries(
            {**{k: st.just(v) for k, v in c.items()}, "required_external_condition": st.just("")}
        )
    )
)
@settings(max_examples=500, suppress_health_check=[HealthCheck.too_slow])
def test_i3_missing_required_external_condition_is_fail_closed(case: dict[str, Any]) -> None:
    result = evaluate_case(case)
    assert result["decision"] == "FAIL_CLOSED", (
        f"Expected FAIL_CLOSED when required_external_condition is empty, got {result['decision']}"
    )


# ---------------------------------------------------------------------------
# I-4: expected_decision != BLOCKED → FAIL_CLOSED (regardless of other fields)
# ---------------------------------------------------------------------------

_forbidden_or_other = st.one_of(
    st.sampled_from(sorted(FORBIDDEN_DECISIONS)),
    st.text(min_size=1, max_size=50).filter(lambda s: s != "BLOCKED" and s.strip()),
)


@given(
    _base_valid_case().flatmap(
        lambda c: _forbidden_or_other.map(
            lambda d: {**c, "expected_decision": d}
        )
    )
)
@settings(max_examples=500, suppress_health_check=[HealthCheck.too_slow])
def test_i4_non_blocked_expected_decision_is_fail_closed(case: dict[str, Any]) -> None:
    result = evaluate_case(case)
    assert result["decision"] == "FAIL_CLOSED", (
        f"Expected FAIL_CLOSED for expected_decision={case['expected_decision']!r}, got {result['decision']}"
    )


# ---------------------------------------------------------------------------
# I-5: built report always has all non_claims fields = False
# ---------------------------------------------------------------------------

def test_i5_all_non_claims_are_false() -> None:
    report = build_report(CASES_PATH)
    non_claims = report.get("non_claims", {})
    for field in NON_CLAIM_FIELDS:
        assert non_claims.get(field) is False, (
            f"non_claims.{field} must be False but got {non_claims.get(field)!r}"
        )


def test_i5_external_flags_are_false() -> None:
    report = build_report(CASES_PATH)
    assert report.get("external_claim_review_completed") is False
    assert report.get("external_validation_pass_claimed") is False
    assert report.get("human_attestation_status") == "HUMAN_ATTESTATION_PENDING"
    boundary = report.get("claim_boundary", {})
    assert boundary.get("external_claim_review_completed") is False
    assert boundary.get("external_validation_pass_claimed") is False


# ---------------------------------------------------------------------------
# I-M (meta): injecting a non-BLOCKED case flips report to FAIL_CLOSED
# ---------------------------------------------------------------------------

@given(
    st.fixed_dictionaries(
        {
            "case_id": st.text(min_size=1, max_size=50),
            "attempted_claim_id": st.text(min_size=1, max_size=100),
            "attempted_claim_text": _nonempty_text,
            "required_external_condition": _nonempty_text,
            "observed_condition": _nonempty_text,
            "expected_decision": st.sampled_from(sorted(FORBIDDEN_DECISIONS)),
            "permitted_alternative": _nonempty_text,
        }
    )
)
@settings(max_examples=200, suppress_health_check=[HealthCheck.too_slow])
def test_im_injected_forbidden_case_causes_report_fail_closed(
    injected: dict[str, Any],
) -> None:
    base_data = json.loads(CASES_PATH.read_text(encoding="utf-8"))
    poisoned = dict(base_data)
    poisoned["cases"] = list(base_data["cases"]) + [injected]

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".json", delete=False, encoding="utf-8"
    ) as tmp:
        json.dump(poisoned, tmp)
        tmp_path = Path(tmp.name)

    try:
        report = build_report(tmp_path)
        assert report["claim_boundary_red_team"] != "PASS", (
            f"Report must not PASS after injecting a case with expected_decision={injected['expected_decision']!r}"
        )
    finally:
        tmp_path.unlink(missing_ok=True)


# ---------------------------------------------------------------------------
# Regression: canonical corpus passes unchanged
# ---------------------------------------------------------------------------

def test_canonical_corpus_all_blocked() -> None:
    report = build_report(CASES_PATH)
    assert report["claim_boundary_red_team"] == "PASS"
    assert report["overclaims_failed_to_block"] == 0
    assert report["block_rate_percent"] == 100.0
    for case in report["cases"]:
        assert case["decision"] == "BLOCKED", (
            f"Canonical case {case['case_id']} must be BLOCKED"
        )
