"""
CEMU swarm containment builder.

Bridge layer for sovereign containment references.
"""

from dataclasses import dataclass
from pathlib import Path


ARTIFACT_CASE_ROOT = Path("artifacts/cases")
CONTAINMENT_STATUS = "SWARM_CONTAINMENT_REFERENCED"


@dataclass(frozen=True, slots=True)
class SwarmContainmentResult:
    case_id: str
    containment_ref: str
    isolation_bundle_ref: str
    status: str

    def referenced_artifacts(self) -> tuple[str, str]:
        return (self.containment_ref, self.isolation_bundle_ref)


def _validate_case_id(case_id: str) -> str:
    normalized = case_id.strip()
    if not normalized:
        raise ValueError("case_id must not be empty")
    if normalized in {".", ".."} or "/" in normalized or "\\" in normalized:
        raise ValueError("case_id must be a single canonical case identifier")
    return normalized


def _artifact_ref(case_id: str, filename: str) -> str:
    return str(ARTIFACT_CASE_ROOT / case_id / filename)


def run_swarm_containment(case_id: str) -> SwarmContainmentResult:
    normalized_case_id = _validate_case_id(case_id)
    return SwarmContainmentResult(
        case_id=normalized_case_id,
        containment_ref=_artifact_ref(
            normalized_case_id,
            f"swarm_containment_state.{normalized_case_id}.canonical.json",
        ),
        isolation_bundle_ref=_artifact_ref(
            normalized_case_id,
            f"post_event_isolation_bundle.{normalized_case_id}.canonical.json",
        ),
        status=CONTAINMENT_STATUS,
    )


def verify_swarm_containment_references(
    result: SwarmContainmentResult,
    repository_root: Path | str = ".",
) -> bool:
    root = Path(repository_root)
    return all((root / artifact_ref).is_file() for artifact_ref in result.referenced_artifacts())


if __name__ == "__main__":
    print(run_swarm_containment("case_003"))
