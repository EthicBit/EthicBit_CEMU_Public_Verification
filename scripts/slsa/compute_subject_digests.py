#!/usr/bin/env python3
"""Bind SHA-256 digests to SLSA subject index entries.

Reads subject-index.json, computes SHA-256 of each referenced file,
and writes a bound copy to --output (default: subject-index-bound.json
in the same directory).
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--subjects",
        type=Path,
        default=REPO_ROOT / "assurance/slsa/subject-index.json",
    )
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()

    index_path = args.subjects.resolve()
    output_path = args.output.resolve() if args.output else index_path.parent / "subject-index-bound.json"

    data = json.loads(index_path.read_text(encoding="utf-8"))
    bound_subjects = []
    for subject in data.get("subjects", []):
        name = subject["name"]
        file_path = REPO_ROOT / name
        if file_path.exists():
            digest = sha256_file(file_path)
            status = "BOUND"
        else:
            digest = None
            status = "FILE_NOT_PRESENT"
        bound_subjects.append({
            "name": name,
            "digest_status": status,
            "sha256": digest,
        })
        print(f"  {status}  {name}" + (f"  sha256={digest[:16]}..." if digest else ""))

    bound = {**data, "subjects": bound_subjects, "binding_status": "BOUND"}
    output_path.write_text(json.dumps(bound, indent=2) + "\n", encoding="utf-8")
    present = sum(1 for s in bound_subjects if s["digest_status"] == "BOUND")
    print(f"\n{present}/{len(bound_subjects)} subjects bound → {output_path.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    main()
