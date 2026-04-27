from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
RESULTS = ROOT / "results"

SNAPSHOT = RESULTS / "mechanical_ethics_snapshot.json"
GUARD = RESULTS / "realtime_millisecond_guard.json"

MAX_AGE_MS = 7000


def canonical_json(obj: dict[str, Any]) -> bytes:
    return json.dumps(
        obj,
        sort_keys=True,
        ensure_ascii=False,
        separators=(",", ":"),
    ).encode("utf-8")


def sha256_obj(obj: dict[str, Any]) -> str:
    payload = dict(obj)
    payload.pop("fingerprint", None)
    return "sha256:" + hashlib.sha256(canonical_json(payload)).hexdigest()


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def fail(reason: str) -> None:
    print("REALTIME_SNAPSHOT_GUARD=FAIL_CLOSED")
    print("reason=" + reason)
    raise SystemExit(1)


def main() -> int:
    if not SNAPSHOT.exists():
        fail("MISSING_MECHANICAL_ETHICS_SNAPSHOT")

    if not GUARD.exists():
        fail("MISSING_REALTIME_MILLISECOND_GUARD")

    snap = load(SNAPSHOT)
    guard = load(GUARD)

    expected_fp = sha256_obj(snap)
    if snap.get("fingerprint") != expected_fp:
        fail("SNAPSHOT_FINGERPRINT_MISMATCH")

    age_ms = (time.time() - SNAPSHOT.stat().st_mtime) * 1000.0
    if age_ms > MAX_AGE_MS:
        fail("STALE_SNAPSHOT")

    required_snapshot = {
        "status": "PASS",
        "mechanical_ethics": "PASS",
        "l5_canonical_state": "PASS",
        "canonical_state": "ACTIVE_CANONICAL",
        "claim_level_ceiling": "L5",
    }

    for key, expected in required_snapshot.items():
        if snap.get(key) != expected:
            fail(f"SNAPSHOT_{key}_EXPECTED_{expected}_GOT_{snap.get(key)}")

    required_guard = {
        "guard": "OK",
        "constitutional_equivalence": True,
        "fingerprint_valid": True,
        "canonical_state": "ACTIVE_CANONICAL",
        "claim_level_ceiling": "L5",
    }

    for key, expected in required_guard.items():
        if guard.get(key) != expected:
            fail(f"GUARD_{key}_EXPECTED_{expected}_GOT_{guard.get(key)}")

    if guard.get("snapshot_age_ms", MAX_AGE_MS + 1) > MAX_AGE_MS:
        fail("GUARD_SNAPSHOT_AGE_EXCEEDS_LIMIT")

    print("REALTIME_SNAPSHOT_GUARD=PASS")
    print("constitutional_equivalence=True")
    print("claim_level_ceiling=L5")
    print("snapshot_age_ms=" + str(round(age_ms, 3)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
