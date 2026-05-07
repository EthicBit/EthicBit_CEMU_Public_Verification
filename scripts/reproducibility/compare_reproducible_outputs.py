#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import platform
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EXPECTED = ROOT / "assurance/reproducibility/expected_hashes.json"
REPORT = ROOT / "assurance/reproducibility/comparison_report.json"
ENV = ROOT / "assurance/reproducibility/environment_fingerprint.json"


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sha256_canonical_json(path: Path) -> str:
    obj = json.loads(path.read_text(encoding="utf-8"))
    data = json.dumps(
        obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def first_line_or_none(cmd: list[str]) -> str | None:
    try:
        out = subprocess.check_output(cmd, text=True, stderr=subprocess.STDOUT).strip()
        return out.splitlines()[0] if out else None
    except Exception:
        return None


def main() -> None:
    expected = json.loads(EXPECTED.read_text(encoding="utf-8"))

    subjects = []
    matched = 0
    mismatched = 0
    placeholders = 0

    for subject in expected.get("subjects", []):
        path = ROOT / subject["path"]
        hash_type = subject["hash_type"]
        expected_sha = subject.get("expected_sha256")

        if not path.exists():
            observed = None
            match = False
            reason = "missing_file"
        else:
            observed = (
                sha256_file(path)
                if hash_type == "file_sha256"
                else sha256_canonical_json(path)
            )
            if expected_sha == "TO_BE_FILLED_FROM_REPO":
                match = None
                reason = "expected_hash_placeholder"
                placeholders += 1
            else:
                match = observed == expected_sha
                reason = "match" if match else "hash_mismatch"

        if match is True:
            matched += 1
        elif match is False:
            mismatched += 1

        subjects.append(
            {
                "id": subject["id"],
                "path": subject["path"],
                "hash_type": hash_type,
                "expected_sha256": expected_sha,
                "observed_sha256": observed,
                "match": match,
                "reason": reason,
            }
        )

    status = "PASS" if mismatched == 0 else "FAIL"
    now = datetime.now(timezone.utc).isoformat()

    report = {
        "schema_id": "AEM_V1_1_REPRODUCIBILITY_COMPARISON_REPORT_V1",
        "status": status,
        "current_closure": "PUBLIC_REPRODUCIBLE_VERIFICATION_SUPPORT",
        "target_closure": "INDEPENDENTLY_REPRODUCED_RELEASE_BUILD",
        "generated_at": now,
        "subjects": subjects,
        "summary": {
            "total": len(subjects),
            "matched": matched,
            "mismatched": mismatched,
            "placeholders": placeholders,
        },
    }

    env = {
        "schema_id": "AEM_V1_1_REPRODUCIBILITY_ENVIRONMENT_FINGERPRINT_V1",
        "status": "GENERATED",
        "generated_at": now,
        "environment": {
            "os": platform.platform(),
            "kernel": platform.release(),
            "architecture": platform.machine(),
            "python_version": platform.python_version(),
            "git_version": first_line_or_none(["git", "--version"]),
            "docker_version": first_line_or_none(["docker", "--version"]),
            "nix_version": first_line_or_none(["nix", "--version"]),
        },
        "notes": "Fingerprint for this reproducibility comparison execution.",
    }

    REPORT.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    ENV.write_text(json.dumps(env, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(f"REPRODUCIBILITY_COMPARISON_STATUS={status}")
    print(f"subjects_total={len(subjects)}")
    print(f"subjects_matched={matched}")
    print(f"subjects_mismatched={mismatched}")
    print(f"subjects_placeholders={placeholders}")


if __name__ == "__main__":
    main()

