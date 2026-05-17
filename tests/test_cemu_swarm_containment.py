from pathlib import Path

import pytest

from cemu.builders.swarm_containment import (
    CONTAINMENT_STATUS,
    run_swarm_containment,
    verify_swarm_containment_references,
)


REPO_ROOT = Path(__file__).resolve().parents[1]


def test_swarm_containment_case_003_references_existing_artifacts() -> None:
    result = run_swarm_containment("case_003")

    assert result.case_id == "case_003"
    assert result.status == CONTAINMENT_STATUS
    assert result.containment_ref == (
        "artifacts/cases/case_003/swarm_containment_state.case_003.canonical.json"
    )
    assert result.isolation_bundle_ref == (
        "artifacts/cases/case_003/post_event_isolation_bundle.case_003.canonical.json"
    )
    assert verify_swarm_containment_references(result, REPO_ROOT)


@pytest.mark.parametrize("case_id", ["", "   ", "../case_003", "case/003", "case\\003"])
def test_swarm_containment_rejects_non_canonical_case_ids(case_id: str) -> None:
    with pytest.raises(ValueError):
        run_swarm_containment(case_id)


def test_swarm_containment_normalizes_outer_whitespace() -> None:
    result = run_swarm_containment(" case_003 ")

    assert result.case_id == "case_003"
    assert verify_swarm_containment_references(result, REPO_ROOT)
