#!/usr/bin/env python3
"""Write periodic audit receipt for scheduler evidence."""

from __future__ import annotations

import argparse
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def now_utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def read_json(path: Path) -> Any:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def git_head(root: Path) -> str:
    try:
        result = subprocess.run(
            ["git", "-C", str(root), "rev-parse", "HEAD"],
            check=False,
            capture_output=True,
            text=True,
        )
    except OSError:
        return "UNKNOWN"
    if result.returncode != 0:
        return "UNKNOWN"
    return (result.stdout or "").strip() or "UNKNOWN"


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate periodic audit receipt")
    parser.add_argument("--root", default=".")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    gate_path = root / "results/GATE_REPORT.json"
    official_path = root / "artifacts/history/swarm/official_operational_status.json"
    out_path = root / "artifacts/history/swarm/periodic_audit_receipt.json"

    gate = read_json(gate_path) or {}
    official = read_json(official_path) or {}

    receipt = {
        "artifactType": "periodic_audit_receipt",
        "generatedAt": now_utc_iso(),
        "scheduler": "github_actions_schedule",
        "gitHead": git_head(root),
        "gateStatus": str((gate.get("verifiedState") or {}).get("operationalReadiness") or "UNKNOWN"),
        "officialStatus": str(official.get("officialStatus") or "UNKNOWN"),
        "officialReason": str(official.get("reason") or "UNKNOWN"),
        "paths": {
            "gateReport": str(gate_path),
            "officialStatus": str(official_path),
            "output": str(out_path),
        },
    }

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(receipt, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(str(out_path))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
