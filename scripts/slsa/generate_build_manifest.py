#!/usr/bin/env python3
"""Generate a SLSA build manifest with provenance metadata.

Captures commit SHA, ref, workflow identity, and artifact digests from
the bound subject index. Writes a manifest that can be signed downstream
by slsa_hybrid_attest.yml.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--commit", default=os.environ.get("GITHUB_SHA", "LOCAL"))
    parser.add_argument("--ref", default=os.environ.get("GITHUB_REF", "refs/heads/main"))
    parser.add_argument("--workflow", default=os.environ.get("GITHUB_WORKFLOW", "slsa-build"))
    parser.add_argument("--run-id", default=os.environ.get("GITHUB_RUN_ID", "LOCAL"))
    parser.add_argument(
        "--bound-subjects",
        type=Path,
        default=REPO_ROOT / "assurance/slsa/subject-index-bound.json",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=REPO_ROOT / "assurance/slsa/build-manifest.json",
    )
    args = parser.parse_args()

    subjects: list[dict] = []
    bound_path = args.bound_subjects.resolve()
    if bound_path.exists():
        bound_data = json.loads(bound_path.read_text(encoding="utf-8"))
        subjects = [
            {"name": s["name"], "digest": {"sha256": s["sha256"]}}
            for s in bound_data.get("subjects", [])
            if s.get("sha256")
        ]

    manifest = {
        "schema_id": "ETHICBIT_SLSA_BUILD_MANIFEST_V1",
        "buildType": "https://slsa.dev/provenance/v1",
        "builder": {
            "id": "https://github.com/EthicBit/EthicBit_CEMU/.github/workflows/slsa-build.yml",
            "version": "v1.0",
        },
        "build": {
            "commit": args.commit,
            "ref": args.ref,
            "workflow": args.workflow,
            "run_id": args.run_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
        "subjects": subjects,
        "materials": [
            {
                "uri": "git+https://github.com/EthicBit/EthicBit_CEMU.git",
                "digest": {"gitCommit": args.commit},
            }
        ],
    }

    output_path = args.output.resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    manifest_sha = hashlib.sha256(output_path.read_bytes()).hexdigest()
    print(f"build-manifest.json written")
    print(f"  commit={args.commit[:12]}  ref={args.ref}")
    print(f"  subjects={len(subjects)}  sha256={manifest_sha[:16]}...")


if __name__ == "__main__":
    main()
