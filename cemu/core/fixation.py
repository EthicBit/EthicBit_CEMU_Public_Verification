"""
CEMU fixation layer.

Transforms reviewed outputs into fixed references.
"""

from dataclasses import dataclass


@dataclass
class FixationRecord:
    case_id: str
    artifact_ref: str
    fixation_status: str


def fix_output(case_id: str, artifact_ref: str) -> FixationRecord:
    return FixationRecord(
        case_id=case_id,
        artifact_ref=artifact_ref,
        fixation_status="FIXED_FOR_SEALING",
    )


if __name__ == "__main__":
    print(fix_output("case_003", "artifacts/cases/case_003/canonical_root.case_003.json"))
