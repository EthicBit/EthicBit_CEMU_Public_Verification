"""
CEMU provenance layer.

Tracks minimal provenance references for incremental v6.0 materialization.
"""

from dataclasses import dataclass
from typing import List


@dataclass
class ProvenanceRecord:
    case_id: str
    source_hashes: List[str]
    lineage_status: str


def build_provenance(case_id: str, source_hashes: List[str]) -> ProvenanceRecord:
    return ProvenanceRecord(
        case_id=case_id,
        source_hashes=source_hashes,
        lineage_status="PROVENANCE_BOUND",
    )


if __name__ == "__main__":
    record = build_provenance("case_003", ["sha256:placeholder"])
    print(record)
