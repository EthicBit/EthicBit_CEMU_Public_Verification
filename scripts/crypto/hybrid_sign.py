#!/usr/bin/env python3
"""Hybrid signature helper (Ed25519 + ML-DSA) using external signer hooks.

Commands are provided as templates with placeholders:
  {payload}   canonical payload file path
  {signature} output signature file path
  {key_id}    key identifier string
  {algorithm} algorithm label
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shlex
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from jcs_rfc8785 import canonicalize_bytes


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _render_command(template: str, *, payload: Path, signature: Path, key_id: str, algorithm: str) -> list[str]:
    rendered = template.format(
        payload=str(payload),
        signature=str(signature),
        key_id=key_id,
        algorithm=algorithm,
    )
    return shlex.split(rendered)


def _command_timeout_seconds() -> float:
    raw = os.environ.get("ETHICBIT_SIGNER_CMD_TIMEOUT_SEC", "25").strip()
    try:
        value = float(raw)
    except Exception:
        return 25.0
    if value <= 0:
        return 25.0
    return value


def _sign_one(
    *,
    algorithm: str,
    command_template: str,
    key_id: str,
    payload_bytes: bytes,
) -> dict[str, Any]:
    result: dict[str, Any] = {
        "algorithm": algorithm,
        "keyId": key_id,
        "status": "FAIL",
        "signature": "",
        "signedAt": _now_utc(),
        "commandConfigured": bool(command_template.strip()),
    }

    if not command_template.strip():
        result["error"] = f"missing signer command for {algorithm}"
        return result

    timeout_seconds = _command_timeout_seconds()
    result["timeoutSeconds"] = timeout_seconds

    with tempfile.TemporaryDirectory(prefix=f"ethicbit_sign_{algorithm.lower()}_") as tmp:
        payload_path = Path(tmp) / "payload.jcs.json"
        signature_path = Path(tmp) / f"{algorithm.lower()}.sig"
        payload_path.write_bytes(payload_bytes)

        cmd = _render_command(
            command_template,
            payload=payload_path,
            signature=signature_path,
            key_id=key_id,
            algorithm=algorithm,
        )

        try:
            proc = subprocess.run(
                cmd,
                check=False,
                capture_output=True,
                text=True,
                timeout=timeout_seconds,
            )
        except subprocess.TimeoutExpired:
            result["error"] = f"signer command timeout after {timeout_seconds}s"
            return result
        if proc.returncode != 0:
            result["error"] = (proc.stderr or proc.stdout or "signer command failed").strip()
            return result

        signature_value = ""
        if signature_path.exists():
            signature_value = signature_path.read_text(encoding="utf-8").strip()
        elif proc.stdout:
            signature_value = proc.stdout.strip()

        if not signature_value:
            result["error"] = "signer command did not produce signature output"
            return result

        result["signature"] = signature_value
        result["status"] = "PASS"
        return result


def build_hybrid_signature_set(
    payload: dict[str, Any],
    *,
    policy_version: str,
    run_context: dict[str, str],
    risk_mode: str,
    ed25519_sign_cmd: str,
    mldsa_sign_cmd: str,
    ed25519_key_id: str,
    mldsa_key_id: str,
    required_algorithms: list[str],
) -> tuple[dict[str, Any], bytes]:
    payload_bytes = canonicalize_bytes(payload)

    signatures = [
        _sign_one(
            algorithm="ED25519",
            command_template=ed25519_sign_cmd,
            key_id=ed25519_key_id,
            payload_bytes=payload_bytes,
        ),
        _sign_one(
            algorithm="ML-DSA",
            command_template=mldsa_sign_cmd,
            key_id=mldsa_key_id,
            payload_bytes=payload_bytes,
        ),
    ]

    status_by_algo = {entry["algorithm"]: entry["status"] for entry in signatures}
    missing = [algo for algo in required_algorithms if status_by_algo.get(algo) != "PASS"]
    status = "PASS" if not missing else "FAIL"

    summary = {
        "status": status,
        "policyVersion": policy_version,
        "riskMode": risk_mode,
        "runContext": run_context,
        "requiredAlgorithms": required_algorithms,
        "payloadHash": _sha256(payload_bytes),
        "signatures": signatures,
    }
    if missing:
        summary["missingOrInvalidAlgorithms"] = missing

    return summary, payload_bytes


def main() -> int:
    parser = argparse.ArgumentParser(description="Sign JSON payload with hybrid signer hooks")
    parser.add_argument("payload", help="Input JSON payload")
    parser.add_argument("--output", required=True, help="Output signature set JSON")
    parser.add_argument("--risk-mode", default=os.environ.get("ETHICBIT_RISK_MODE", "HIGH"))
    parser.add_argument("--policy-version", default="official-operational-status-policy.v2.0.0")
    parser.add_argument("--ed25519-sign-cmd", default=os.environ.get("ETHICBIT_ED25519_SIGN_CMD", ""))
    parser.add_argument("--mldsa-sign-cmd", default=os.environ.get("ETHICBIT_MLDSA_SIGN_CMD", ""))
    parser.add_argument("--ed25519-key-id", default=os.environ.get("ETHICBIT_ED25519_KEY_ID", "ED25519_UNSET"))
    parser.add_argument("--mldsa-key-id", default=os.environ.get("ETHICBIT_MLDSA_KEY_ID", "MLDSA_UNSET"))
    args = parser.parse_args()

    payload = json.loads(Path(args.payload).read_text(encoding="utf-8"))
    risk_mode = args.risk_mode.upper().strip() or "HIGH"
    required = ["ED25519"] if risk_mode == "STANDARD" else ["ED25519", "ML-DSA"]

    signature_set, _ = build_hybrid_signature_set(
        payload,
        policy_version=args.policy_version,
        run_context={"runId": "CLI", "releaseId": "CLI", "verificationEpoch": "CLI"},
        risk_mode=risk_mode,
        ed25519_sign_cmd=args.ed25519_sign_cmd,
        mldsa_sign_cmd=args.mldsa_sign_cmd,
        ed25519_key_id=args.ed25519_key_id,
        mldsa_key_id=args.mldsa_key_id,
        required_algorithms=required,
    )

    Path(args.output).write_text(json.dumps(signature_set, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(signature_set["status"])
    return 0 if signature_set["status"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
