"""
CEMU core intake layer.

Initial minimal implementation for v6.0 incremental materialization.
"""

from dataclasses import dataclass
from typing import Any, Dict


@dataclass
class IntakeRecord:
    case_id: str
    source_ref: str
    status: str
    metadata: Dict[str, Any]


def register_intake(case_id: str, source_ref: str, metadata: Dict[str, Any] | None = None) -> IntakeRecord:
    return IntakeRecord(
        case_id=case_id,
        source_ref=source_ref,
        status="INTAKE_REGISTERED",
        metadata=metadata or {},
    )


if __name__ == "__main__":
    record = register_intake("case_003", "local/materialized-artifacts")
    print(record)
