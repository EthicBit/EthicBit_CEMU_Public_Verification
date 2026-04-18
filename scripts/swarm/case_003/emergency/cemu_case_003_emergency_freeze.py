# scripts/swarm/case_003/emergency/cemu_case_003_emergency_freeze.py
# ETHICBIT / CEMU – CASE 003
# Emergency Freeze / Rollback Marker

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict


CASE_ID = "case_003"
BASE_DIR = Path(__file__).resolve().parents[4]
ARTIFACTS_DIR = BASE_DIR / "artifacts" / "cases" / CASE_ID
ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def write_json(filename: str, payload: Dict[str, Any]) -> Path:
    path = ARTIFACTS_DIR / filename
    with path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)
    return path


def main() -> None:
    parser = argparse.ArgumentParser(description="Emergency freeze marker for Case 003.")
    parser.add_argument("--phase", required=True, help="Phase number triggering emergency freeze.")
    parser.add_argument("--tx", default=None, help="Optional transaction hash if failure occurred onchain.")
    parser.add_argument("--reason", default="MANUAL_OR_AUTOMATIC_EMERGENCY_FREEZE", help="Freeze reason.")
    args = parser.parse_args()

    payload = {
        "case_id": CASE_ID,
        "emergency_freeze_id": f"{CASE_ID}-EMERGENCY-FREEZE-{args.phase}",
        "phase": args.phase,
        "tx_hash": args.tx,
        "reason": args.reason,
        "status": "EMERGENCY_FREEZE_TRIGGERED",
        "generated_at": now_iso(),
    }

    out = write_json(f"emergency_freeze_phase_{args.phase}.case_003.canonical.json", payload)

    print("=" * 88)
    print("ETHICBIT / CEMU – CASE 003 EMERGENCY FREEZE")
    print("=" * 88)
    print(f"Phase:                  {args.phase}")
    print(f"TX Hash:                {args.tx}")
    print(f"Reason:                 {args.reason}")
    print(f"Artifact written:       {out}")
    print("=" * 88)


if __name__ == "__main__":
    main()
