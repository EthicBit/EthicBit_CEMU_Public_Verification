#!/usr/bin/env python3
"""Emit anti reverse-engineering hardening posture artifact."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DEFAULT_POLICY = {
    "schema_id": "ETHICBIT_ANTI_RE_POLICY_V1",
    "version": "1.0.0",
    "strictClaimLevels": ["freeze_grade", "sovereign_release"],
    "forbiddenEnvVars": ["LD_PRELOAD", "DYLD_INSERT_LIBRARIES"],
    "requireRealtimeGuardOk": True,
    "requireSnapshotFingerprintValid": True,
    "keyPostureByClaimLevel": {
        "default": {
            "allowedStatuses": [
                "TRANSITIONAL_COMPLIANT",
                "SOVEREIGN_COMPLIANT",
                "PRODUCTION_HSM_READY",
            ]
        }
    },
}


def now_utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def load_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None
    return payload if isinstance(payload, dict) else None


def canonical_json_bytes(payload: dict[str, Any]) -> bytes:
    return json.dumps(
        payload,
        sort_keys=True,
        ensure_ascii=False,
        separators=(",", ":"),
    ).encode("utf-8")


def snapshot_fingerprint(payload: dict[str, Any]) -> str:
    copy_payload = dict(payload)
    copy_payload.pop("fingerprint", None)
    digest = hashlib.sha256(canonical_json_bytes(copy_payload)).hexdigest()
    return "sha256:" + digest


def read_tracer_pid() -> int | None:
    status_file = Path("/proc/self/status")
    if not status_file.exists():
        return None
    try:
        for line in status_file.read_text(encoding="utf-8").splitlines():
            if line.startswith("TracerPid:"):
                return int(line.split(":", 1)[1].strip())
    except Exception:
        return None
    return None


def policy_allowed_key_statuses(policy: dict[str, Any], claim_level: str) -> set[str]:
    by_claim = policy.get("keyPostureByClaimLevel")
    if not isinstance(by_claim, dict):
        by_claim = {}

    selected = by_claim.get(claim_level) or by_claim.get("default") or {}
    statuses = selected.get("allowedStatuses") if isinstance(selected, dict) else []
    if not isinstance(statuses, list):
        statuses = []
    normalized = {str(value).strip().upper() for value in statuses if str(value).strip()}
    return normalized


def main() -> int:
    parser = argparse.ArgumentParser(description="Emit anti reverse-engineering guard report")
    parser.add_argument("--root", default=".", help="Repository root path")
    parser.add_argument("--output", default="results/anti_re_guard_report.json", help="Output artifact path")
    parser.add_argument("--policy", default="config/anti_re_policy.v1.json", help="Anti-RE policy path")
    parser.add_argument("--snapshot", default="results/mechanical_ethics_snapshot.json", help="Snapshot artifact path")
    parser.add_argument("--realtime-guard", default="results/realtime_millisecond_guard.json", help="Realtime guard artifact path")
    parser.add_argument("--key-posture", default="results/key_posture_report.json", help="Key posture artifact path")
    parser.add_argument("--claim-level", default=os.environ.get("ETHICBIT_CLAIM_LEVEL", "ci_grade"), help="Claim level")
    parser.add_argument(
        "--no-refresh-realtime-guard",
        action="store_true",
        help="Disable realtime guard refresh before evaluating Anti-RE posture",
    )
    parser.add_argument("--enforce", action="store_true", help="Return non-zero when status is FAIL_CLOSED")
    args = parser.parse_args()

    root = Path(args.root).resolve()

    def resolve(path_value: str) -> Path:
        path = Path(path_value)
        return path if path.is_absolute() else (root / path).resolve()

    output_path = resolve(args.output)
    policy_path = resolve(args.policy)
    snapshot_path = resolve(args.snapshot)
    realtime_guard_path = resolve(args.realtime_guard)
    key_posture_path = resolve(args.key_posture)
    realtime_guard_script = (root / "scripts" / "realtime" / "realtime_snapshot_guard.py").resolve()

    claim_level = str(args.claim_level or "ci_grade").strip() or "ci_grade"

    policy = load_json(policy_path) or dict(DEFAULT_POLICY)
    strict_claim_levels = {
        str(value).strip()
        for value in policy.get("strictClaimLevels", DEFAULT_POLICY["strictClaimLevels"])
        if str(value).strip()
    }
    strict_required = claim_level in strict_claim_levels

    hard_failures: list[str] = []
    warnings: list[str] = []

    checks: dict[str, str] = {
        "snapshot_integrity": "UNKNOWN",
        "snapshot_freshness": "UNKNOWN",
        "runtime_hook_debugger": "UNKNOWN",
        "key_posture": "UNKNOWN",
    }

    if not args.no_refresh_realtime_guard and realtime_guard_script.exists():
        refresh = subprocess.run(
            [sys.executable, str(realtime_guard_script)],
            cwd=str(root),
            text=True,
            capture_output=True,
            timeout=30.0,
            check=False,
        )
        if refresh.returncode != 0:
            if strict_required:
                hard_failures.append("REALTIME_GUARD_REFRESH_FAILED")
            else:
                warnings.append("REALTIME_GUARD_REFRESH_FAILED")

    # Check 1: runtime hook / debugger indicators
    forbidden_env_vars = policy.get("forbiddenEnvVars", DEFAULT_POLICY["forbiddenEnvVars"])
    if not isinstance(forbidden_env_vars, list):
        forbidden_env_vars = DEFAULT_POLICY["forbiddenEnvVars"]

    env_hits: list[str] = []
    for name in forbidden_env_vars:
        key = str(name).strip()
        if not key:
            continue
        raw = os.environ.get(key, "")
        if isinstance(raw, str) and raw.strip():
            env_hits.append(key)

    tracer_pid = read_tracer_pid()
    debugger_attached = sys.gettrace() is not None
    if env_hits or (tracer_pid is not None and tracer_pid > 0) or debugger_attached:
        checks["runtime_hook_debugger"] = "FAIL"
        if env_hits:
            hard_failures.append("RUNTIME_HOOK_ENV_VARS_DETECTED")
        if tracer_pid is not None and tracer_pid > 0:
            hard_failures.append("RUNTIME_TRACERPID_DETECTED")
        if debugger_attached:
            hard_failures.append("RUNTIME_DEBUGGER_DETECTED")
    else:
        checks["runtime_hook_debugger"] = "PASS"

    # Check 2: snapshot integrity + freshness
    snapshot = load_json(snapshot_path)
    if snapshot is None:
        if strict_required:
            checks["snapshot_integrity"] = "FAIL"
            checks["snapshot_freshness"] = "FAIL"
            hard_failures.append("SNAPSHOT_MISSING_OR_UNREADABLE")
        else:
            checks["snapshot_integrity"] = "WARN"
            checks["snapshot_freshness"] = "WARN"
            warnings.append("SNAPSHOT_MISSING_OR_UNREADABLE")
    else:
        status = str(snapshot.get("status") or "").upper()
        expected = snapshot_fingerprint(snapshot)
        observed = str(snapshot.get("fingerprint") or "")
        require_fp = bool(policy.get("requireSnapshotFingerprintValid", True))

        if status != "PASS":
            if strict_required:
                checks["snapshot_integrity"] = "FAIL"
                hard_failures.append("SNAPSHOT_STATUS_NOT_PASS")
            else:
                checks["snapshot_integrity"] = "WARN"
                warnings.append("SNAPSHOT_STATUS_NOT_PASS")
        elif require_fp and observed != expected:
            checks["snapshot_integrity"] = "FAIL"
            hard_failures.append("SNAPSHOT_FINGERPRINT_MISMATCH")
        else:
            checks["snapshot_integrity"] = "PASS"

        valid_until = snapshot.get("valid_until")
        if valid_until is None:
            if strict_required:
                checks["snapshot_freshness"] = "FAIL"
                hard_failures.append("SNAPSHOT_VALID_UNTIL_MISSING")
            else:
                checks["snapshot_freshness"] = "WARN"
                warnings.append("SNAPSHOT_VALID_UNTIL_MISSING")
        else:
            try:
                valid_until_f = float(valid_until)
            except Exception:
                valid_until_f = -1.0

            if valid_until_f <= 0:
                checks["snapshot_freshness"] = "FAIL"
                hard_failures.append("SNAPSHOT_VALID_UNTIL_INVALID")
            elif time.time() > valid_until_f:
                if strict_required:
                    checks["snapshot_freshness"] = "FAIL"
                    hard_failures.append("SNAPSHOT_STALE")
                else:
                    checks["snapshot_freshness"] = "WARN"
                    warnings.append("SNAPSHOT_STALE")
            else:
                checks["snapshot_freshness"] = "PASS"

    # Check 3: realtime guard
    require_guard_ok = bool(policy.get("requireRealtimeGuardOk", True))
    realtime_guard = load_json(realtime_guard_path)
    if require_guard_ok:
        if realtime_guard is None:
            if strict_required:
                hard_failures.append("REALTIME_GUARD_MISSING")
            else:
                warnings.append("REALTIME_GUARD_MISSING")
        else:
            guard_state = str(realtime_guard.get("guard") or "").upper()
            eq = bool(realtime_guard.get("constitutional_equivalence") is True)
            if guard_state != "OK" or not eq:
                if strict_required:
                    hard_failures.append("REALTIME_GUARD_NOT_OK")
                else:
                    warnings.append("REALTIME_GUARD_NOT_OK")

    # Check 4: key posture threshold by claim level
    key_posture = load_json(key_posture_path)
    allowed_key_statuses = policy_allowed_key_statuses(policy, claim_level)

    if key_posture is None:
        if strict_required:
            checks["key_posture"] = "FAIL"
            hard_failures.append("KEY_POSTURE_ARTIFACT_MISSING")
        else:
            checks["key_posture"] = "NOT_REQUIRED"
            warnings.append("KEY_POSTURE_ARTIFACT_MISSING")
    else:
        posture_status = str(key_posture.get("status") or "UNKNOWN").upper()
        if posture_status in allowed_key_statuses:
            checks["key_posture"] = "PASS"
        elif strict_required:
            checks["key_posture"] = "FAIL"
            hard_failures.append(f"KEY_POSTURE_BELOW_THRESHOLD:{posture_status}")
        else:
            checks["key_posture"] = "NOT_REQUIRED"
            warnings.append(f"KEY_POSTURE_BELOW_THRESHOLD:{posture_status}")

    if hard_failures:
        status = "FAIL_CLOSED"
    elif warnings and not strict_required:
        status = "NOT_REQUIRED_FOR_CURRENT_CLAIM"
    else:
        status = "PASS"

    payload = {
        "artifactType": "anti_re_guard_report",
        "schemaVersion": "1.0.0",
        "generatedAt": now_utc_iso(),
        "status": status,
        "claim_level": claim_level,
        "policy_version": str(policy.get("schema_id") or DEFAULT_POLICY["schema_id"]),
        "strict_required": strict_required,
        "checks": checks,
        "failures": hard_failures,
        "warnings": warnings,
        "evidence_ref": {
            "policy": str(policy_path),
            "snapshot": str(snapshot_path),
            "realtime_guard": str(realtime_guard_path),
            "key_posture": str(key_posture_path),
        },
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(str(output_path))
    print("status=" + status)

    if args.enforce and status == "FAIL_CLOSED":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
