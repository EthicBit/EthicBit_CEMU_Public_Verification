#!/usr/bin/env python3
"""Generate and validate hermetic build posture evidence for closure gating."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

SCHEMA_ID = "ETHICBIT_HERMETIC_BUILD_REPORT_V1"
VERSION = "1.0.0"


def now_utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def is_pinned_image_ref(value: str) -> bool:
    if "@sha256:" not in value:
        return False
    digest = value.rsplit("@sha256:", 1)[-1]
    return len(digest) == 64 and all(ch in "0123456789abcdef" for ch in digest)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            chunk = handle.read(65536)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True)
    parser.add_argument(
        "--mode",
        required=True,
        choices=("strict_hermetic", "equivalence_non_hermetic"),
    )
    parser.add_argument("--base-image-ref", required=True)
    parser.add_argument("--network-mode", required=True)
    parser.add_argument("--claim-level", default="ci_grade")
    parser.add_argument("--build-system", default="docker")
    parser.add_argument("--build-target", default="hermetic-check")
    parser.add_argument("--probe-exit-code", type=int, default=0)
    parser.add_argument("--strict-required", action="store_true")
    parser.add_argument("--declared-gap", default="")
    parser.add_argument("--lockfile", action="append", default=[])
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    output_path = Path(args.output).resolve()

    if not args.lockfile:
        raise SystemExit("At least one --lockfile is required")

    lockfiles = []
    missing_lockfiles = []
    for rel_path in args.lockfile:
        lock_path = Path(rel_path).resolve()
        exists = lock_path.is_file()
        lockfiles.append(
            {
                "path": rel_path,
                "exists": exists,
                "sha256": sha256_file(lock_path) if exists else None,
            }
        )
        if not exists:
            missing_lockfiles.append(rel_path)

    pinned_digest = is_pinned_image_ref(args.base_image_ref)
    network_none = args.network_mode == "none"
    lockfiles_verified = len(missing_lockfiles) == 0

    if args.probe_exit_code != 0:
        raise SystemExit(f"Hermetic probe failed with exit code {args.probe_exit_code}")

    if args.strict_required and args.mode != "strict_hermetic":
        raise SystemExit("Strict hermetic mode is required but mode is not strict_hermetic")

    if args.mode == "strict_hermetic":
        if not network_none:
            raise SystemExit("strict_hermetic mode requires network-mode none")
        if not pinned_digest:
            raise SystemExit("strict_hermetic mode requires base image pinned with @sha256")
        if not lockfiles_verified:
            raise SystemExit(
                "strict_hermetic mode requires all lockfiles to exist: "
                + ",".join(missing_lockfiles)
            )
        status = "PASS_STRICT_HERMETIC"
        declared_gap = ""
    else:
        if not args.declared_gap.strip():
            raise SystemExit("equivalence_non_hermetic mode requires --declared-gap")
        status = "PASS_EQUIVALENCE_NON_HERMETIC"
        declared_gap = args.declared_gap.strip()

    report = {
        "schema_id": SCHEMA_ID,
        "version": VERSION,
        "generated_at": now_utc_iso(),
        "status": status,
        "hermetic_mode": args.mode,
        "claim_level": args.claim_level,
        "strict_required": args.strict_required,
        "build_system": args.build_system,
        "build_target": args.build_target,
        "network_mode": args.network_mode,
        "base_image_ref": args.base_image_ref,
        "base_image_pinned_digest": pinned_digest,
        "controls": {
            "network_none_verified": network_none,
            "pinned_base_image_verified": pinned_digest,
            "lockfiles_verified": lockfiles_verified,
        },
        "lockfiles": lockfiles,
        "declared_gap": declared_gap,
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(str(output_path))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
