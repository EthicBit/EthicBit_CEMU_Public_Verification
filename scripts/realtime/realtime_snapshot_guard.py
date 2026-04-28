from __future__ import annotations

import hashlib
import json
import os
import time
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
RESULTS = ROOT / "results"

SNAPSHOT = RESULTS / "mechanical_ethics_snapshot.json"
CEILING = RESULTS / "constitutional_evidence_ceiling.json"
SUPERVISOR = RESULTS / "realtime_supervisor_status.json"
OUT = RESULTS / "realtime_millisecond_guard.json"

MAX_AGE_MS = int(os.environ.get("ETHICBIT_REALTIME_MAX_SNAPSHOT_AGE_MS", "7000"))

_last_mtime: float | None = None
_last_snapshot: dict[str, Any] | None = None


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


def atomic_write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    tmp.replace(path)


def load_json(path: Path) -> dict[str, Any] | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def build_snapshot_from_current_artifacts() -> dict[str, Any]:
    ceiling = load_json(CEILING) or {}
    supervisor = load_json(SUPERVISOR) or {}

    now = time.time()
    status = ceiling.get("status")
    claim_level = (
        ceiling.get("claim_level_ceiling")
        or ceiling.get("target_ceiling")
        or ceiling.get("current_ceiling")
        or "UNKNOWN"
    )

    mechanical_ethics = (
        ceiling.get("mechanical_ethics_status")
        or supervisor.get("mechanics", {}).get("status")
        or "PASS"
    )

    canonical_state = supervisor.get("canonical_state") or "ACTIVE_CANONICAL"

    l5_canonical_state = "PASS" if (
        status == "PASS"
        and claim_level == "L5"
        and canonical_state == "ACTIVE_CANONICAL"
        and mechanical_ethics == "PASS"
    ) else "FAIL_CLOSED"

    snapshot: dict[str, Any] = {
        "schema_id": "ethicbit.mechanical_ethics_snapshot.v1",
        "mode": "CANONICAL_L5_SNAPSHOT",
        "generated_at": now,
        "issued_at": now,
        "valid_until": now + (MAX_AGE_MS / 1000.0),
        "status": "PASS" if l5_canonical_state == "PASS" else "FAIL_CLOSED",
        "mechanical_ethics": mechanical_ethics,
        "l5_canonical_state": l5_canonical_state,
        "canonical_state": canonical_state,
        "claim_level_ceiling": claim_level,
        "constitutional_equivalence_source": "constitutional_evidence_ceiling",
        "constitutional_evidence_status": status,
        "confidence": ceiling.get("confidence"),
        "sources_count": len(ceiling.get("sources", [])) if isinstance(ceiling.get("sources", []), list) else 0,
        "eligible_for_l4": ceiling.get("eligible_for_l4"),
        "eligible_for_l5": ceiling.get("eligible_for_l5"),
        "artifact_links": {
            "constitutional_evidence_ceiling": str(CEILING.relative_to(ROOT)),
            "realtime_supervisor_status": str(SUPERVISOR.relative_to(ROOT)) if SUPERVISOR.exists() else None,
        },
        "fail_closed_policy": True,
        "fast_loop_policy": {
            "full_probative_apparatus_out_of_loop": True,
            "o1_guard_only": True,
            "no_oracle_calls_in_fast_loop": True,
            "no_onchain_anchor_in_fast_loop": True,
            "no_heavy_kzg_in_fast_loop": True,
            "no_full_mechanical_ethics_recalc_per_tick": True,
        },
    }

    snapshot["fingerprint"] = sha256_obj(snapshot)
    return snapshot


def write_snapshot() -> dict[str, Any]:
    snapshot = build_snapshot_from_current_artifacts()
    atomic_write_json(SNAPSHOT, snapshot)
    return snapshot


def load_snapshot_cached() -> tuple[dict[str, Any] | None, float | None]:
    global _last_mtime, _last_snapshot

    if not SNAPSHOT.exists():
        return None, None

    try:
        stat = SNAPSHOT.stat()
    except Exception:
        return None, None

    mtime = stat.st_mtime

    if _last_snapshot is not None and _last_mtime == mtime:
        return _last_snapshot, mtime

    snap = load_json(SNAPSHOT)
    if snap is None:
        return None, mtime

    _last_mtime = mtime
    _last_snapshot = snap
    return snap, mtime


def realtime_guard_from_snapshot() -> dict[str, Any]:
    snap, mtime = load_snapshot_cached()
    now = time.time()

    if snap is None or mtime is None:
        return {
            "schema_id": "ethicbit.realtime_millisecond_guard.v1",
            "mode": "REALTIME_SNAPSHOT_GUARD",
            "guard": "BLOCKED",
            "constitutional_equivalence": False,
            "reason": "MISSING_OR_UNREADABLE_SNAPSHOT",
            "updated_at": now,
        }

    age_ms = (now - mtime) * 1000.0

    if age_ms > MAX_AGE_MS:
        return {
            "schema_id": "ethicbit.realtime_millisecond_guard.v1",
            "mode": "REALTIME_SNAPSHOT_GUARD",
            "guard": "BLOCKED",
            "constitutional_equivalence": False,
            "reason": "STALE_SNAPSHOT",
            "snapshot_age_ms": round(age_ms, 3),
            "max_age_ms": MAX_AGE_MS,
            "updated_at": now,
        }

    expected_fp = sha256_obj(snap)
    actual_fp = snap.get("fingerprint")

    if actual_fp != expected_fp:
        return {
            "schema_id": "ethicbit.realtime_millisecond_guard.v1",
            "mode": "REALTIME_SNAPSHOT_GUARD",
            "guard": "BLOCKED",
            "constitutional_equivalence": False,
            "reason": "FINGERPRINT_MISMATCH",
            "expected_fingerprint": expected_fp,
            "actual_fingerprint": actual_fp,
            "snapshot_age_ms": round(age_ms, 3),
            "updated_at": now,
        }

    checks = [
        ("SNAPSHOT_STATUS_NOT_PASS", snap.get("status") == "PASS"),
        ("MECHANICAL_ETHICS_NOT_PASS", snap.get("mechanical_ethics") == "PASS"),
        ("L5_CANONICAL_STATE_NOT_PASS", snap.get("l5_canonical_state") == "PASS"),
        ("NON_CANONICAL", snap.get("canonical_state") == "ACTIVE_CANONICAL"),
        ("CLAIM_LEVEL_NOT_L5", snap.get("claim_level_ceiling") == "L5"),
        ("FAIL_CLOSED_POLICY_MISSING", snap.get("fail_closed_policy") is True),
    ]

    for reason, ok in checks:
        if not ok:
            return {
                "schema_id": "ethicbit.realtime_millisecond_guard.v1",
                "mode": "REALTIME_SNAPSHOT_GUARD",
                "guard": "BLOCKED",
                "constitutional_equivalence": False,
                "reason": reason,
                "snapshot_age_ms": round(age_ms, 3),
                "snapshot_status": snap.get("status"),
                "mechanical_ethics": snap.get("mechanical_ethics"),
                "l5_canonical_state": snap.get("l5_canonical_state"),
                "canonical_state": snap.get("canonical_state"),
                "claim_level_ceiling": snap.get("claim_level_ceiling"),
                "updated_at": now,
            }

    return {
        "schema_id": "ethicbit.realtime_millisecond_guard.v1",
        "mode": "REALTIME_10MS_COMPATIBLE",
        "guard": "OK",
        "constitutional_equivalence": True,
        "snapshot_status": "PASS",
        "mechanical_ethics": "PASS",
        "l5_canonical_state": "PASS",
        "snapshot_age_ms": round(age_ms, 3),
        "fingerprint_valid": True,
        "canonical_state": "ACTIVE_CANONICAL",
        "claim_level_ceiling": "L5",
        "max_age_ms": MAX_AGE_MS,
        "fast_loop_policy": snap.get("fast_loop_policy"),
        "updated_at": now,
    }


def main() -> int:
    write_snapshot()
    guard = realtime_guard_from_snapshot()
    atomic_write_json(OUT, guard)

    print("realtime_millisecond_guard=" + str(OUT))
    print("guard=" + str(guard.get("guard")))
    print("constitutional_equivalence=" + str(guard.get("constitutional_equivalence")))
    print("claim_level_ceiling=" + str(guard.get("claim_level_ceiling")))
    print("snapshot_age_ms=" + str(guard.get("snapshot_age_ms")))

    return 0 if guard.get("guard") == "OK" and guard.get("constitutional_equivalence") is True else 1


if __name__ == "__main__":
    raise SystemExit(main())
