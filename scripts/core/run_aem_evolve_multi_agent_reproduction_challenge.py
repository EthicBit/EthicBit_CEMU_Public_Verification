#!/usr/bin/env python3
"""
AEM-EVOLVE Multi-Agent Governance API — Independent Reproduction Challenge Runner.

Verifies that all declared subjects in the reproduction challenge package match
their expected SHA-256 hashes at the current working tree state.

This is a file-integrity check only. It does NOT:
  - Run the API server
  - Execute E2E tests (use run_demo_e2e.sh for that)
  - Verify signatures (use verify_demo_receipt_signatures.sh for that)
  - Verify the audit chain (use verify_aem_evolve_multi_agent_audit_chain.py for that)

Usage:
  python run_aem_evolve_multi_agent_reproduction_challenge.py [challenge_json]

  challenge_json defaults to:
    assurance/evolve-multi-agent/AEM_EVOLVE_MULTI_AGENT_API_REPRODUCTION_CHALLENGE.json

Exit codes:
  0  ALL_MATCH — all declared hashes verified
  1  MISMATCH_DETECTED or ERROR
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CHALLENGE = (
    ROOT
    / "assurance"
    / "evolve-multi-agent"
    / "AEM_EVOLVE_MULTI_AGENT_API_REPRODUCTION_CHALLENGE.json"
)


def run(challenge_path: Path) -> int:
    if not challenge_path.exists():
        print(f"ERROR: challenge file not found: {challenge_path}", file=sys.stderr)
        return 1

    challenge = json.loads(challenge_path.read_text(encoding="utf-8"))
    subjects = challenge.get("subjects", [])

    print("=== AEM-EVOLVE MULTI-AGENT API REPRODUCTION CHALLENGE ===")
    print(f"challenge_path   = {challenge_path}")
    print(f"source_commit    = {challenge.get('source_commit')}")
    print(f"subjects_count   = {len(subjects)}")
    print(f"status           = {challenge.get('status')}")
    print("")

    mismatches: list[dict] = []
    missing: list[str] = []

    for subject in subjects:
        path_rel = subject["path"]
        expected = subject["sha256"]
        role = subject.get("role", "")
        full_path = ROOT / path_rel

        if not full_path.exists():
            missing.append(path_rel)
            print(f"  MISSING  {path_rel}")
            continue

        computed = hashlib.sha256(full_path.read_bytes()).hexdigest()
        ok = computed == expected
        status = "MATCH  " if ok else "MISMATCH"
        print(f"  {status}  [{role:<28s}]  {path_rel}")

        if not ok:
            mismatches.append({
                "path": path_rel,
                "expected": expected,
                "computed": computed,
            })

    print("")
    print(f"subjects_total   = {len(subjects)}")
    print(f"matched          = {len(subjects) - len(mismatches) - len(missing)}")
    print(f"mismatches       = {len(mismatches)}")
    print(f"missing          = {len(missing)}")

    if mismatches:
        print("\nMISMATCH DETAILS:")
        for m in mismatches:
            print(f"  path     = {m['path']}")
            print(f"  expected = {m['expected']}")
            print(f"  computed = {m['computed']}")
            print()

    if missing:
        print("\nMISSING FILES:")
        for f in missing:
            print(f"  {f}")

    print("")
    if not mismatches and not missing:
        print("AEM_EVOLVE_REPRODUCTION_CHALLENGE_STATUS=ALL_MATCH")
        print("NOTE: File-integrity check only. Independent reproduction requires")
        print("      separate environment or third-party execution.")
        return 0

    print("AEM_EVOLVE_REPRODUCTION_CHALLENGE_STATUS=FAIL")
    return 1


if __name__ == "__main__":
    challenge_path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_CHALLENGE
    raise SystemExit(run(challenge_path))
