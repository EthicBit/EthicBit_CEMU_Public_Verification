#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
COMPARISON = ROOT / "assurance/reproducibility/comparison_report.json"
REPORT = ROOT / "assurance/reproducibility/independent_reproduction_report.json"


def git_ref() -> str | None:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"], text=True
        ).strip()
    except Exception:
        return None


def main() -> None:
    comparison = json.loads(COMPARISON.read_text(encoding="utf-8"))
    mismatched = comparison.get("summary", {}).get("mismatched")
    all_matched = mismatched == 0 if isinstance(mismatched, int) else None

    report = {
        "schema_id": "AEM_V1_1_INDEPENDENT_REPRODUCTION_REPORT_V1",
        "status": "LOCAL_PREPARATION_REPORT_NOT_INDEPENDENT_ATTESTATION",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "current_closure": "PUBLIC_REPRODUCIBLE_VERIFICATION_SUPPORT",
        "target_closure": "INDEPENDENTLY_REPRODUCED_RELEASE_BUILD",
        "independent_reproduction_claimed": False,
        "third_party_reproduction_completed": False,
        "source": {
            "repository": "EthicBit/EthicBit_CEMU",
            "commit_or_tag": git_ref(),
        },
        "result": {
            "local_comparison_status": comparison.get("status"),
            "hash_comparison_completed": True,
            "all_declared_subjects_matched": all_matched,
        },
        "notes": "Local preparation report only. Independent reproduction requires separate environment or third-party execution.",
    }

    REPORT.write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print("REPRODUCIBILITY_REPORT_GENERATED=YES")
    print("independent_reproduction_claimed=false")
    print("third_party_reproduction_completed=false")


if __name__ == "__main__":
    main()

