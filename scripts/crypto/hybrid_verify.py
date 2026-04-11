#!/usr/bin/env python3
"""Hybrid signature verification helper (Ed25519 + ML-DSA)."""

from __future__ import annotations

import argparse
import json
import os
import shlex
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from jcs_rfc8785 import canonicalize_bytes


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


def _verify_one(
    *,
    algorithm: str,
    signature_entry: dict[str, Any],
    verify_command_template: str,
    payload_bytes: bytes,
) -> dict[str, Any]:
    result: dict[str, Any] = {
        "algorithm": algorithm,
        "status": "FAIL",
        "commandConfigured": bool(verify_command_template.strip()),
    }

    signature_value = str(signature_entry.get("signature") or "").strip()
    key_id = str(signature_entry.get("keyId") or "UNSET")
    if not signature_value:
        result["error"] = "missing signature value"
        return result

    if not verify_command_template.strip():
        result["error"] = f"missing verify command for {algorithm}"
        return result

    timeout_seconds = _command_timeout_seconds()
    result["timeoutSeconds"] = timeout_seconds

    with tempfile.TemporaryDirectory(prefix=f"ethicbit_verify_{algorithm.lower()}_") as tmp:
        payload_path = Path(tmp) / "payload.jcs.json"
        signature_path = Path(tmp) / f"{algorithm.lower()}.sig"
        payload_path.write_bytes(payload_bytes)
        signature_path.write_text(signature_value + "\n", encoding="utf-8")

        cmd = _render_command(
            verify_command_template,
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
            result["error"] = f"verify command timeout after {timeout_seconds}s"
            return result
        if proc.returncode != 0:
            result["error"] = (proc.stderr or proc.stdout or "verify command failed").strip()
            return result

        result["status"] = "PASS"
        return result


def verify_hybrid_signature_set(
    payload: dict[str, Any],
    signature_set: dict[str, Any],
    *,
    risk_mode: str,
    ed25519_verify_cmd: str,
    mldsa_verify_cmd: str,
    required_algorithms: list[str],
) -> dict[str, Any]:
    payload_bytes = canonicalize_bytes(payload)

    signatures = signature_set.get("signatures")
    if not isinstance(signatures, list):
        return {
            "status": "FAIL",
            "error": "signature_set.signatures must be an array",
            "requiredAlgorithms": required_algorithms,
            "riskMode": risk_mode,
        }

    by_algo: dict[str, dict[str, Any]] = {}
    for entry in signatures:
        if isinstance(entry, dict):
            algo = str(entry.get("algorithm") or "").upper()
            if algo:
                by_algo[algo] = entry

    checks: list[dict[str, Any]] = []
    checks.append(
        _verify_one(
            algorithm="ED25519",
            signature_entry=by_algo.get("ED25519", {}),
            verify_command_template=ed25519_verify_cmd,
            payload_bytes=payload_bytes,
        )
    )
    checks.append(
        _verify_one(
            algorithm="ML-DSA",
            signature_entry=by_algo.get("ML-DSA", {}),
            verify_command_template=mldsa_verify_cmd,
            payload_bytes=payload_bytes,
        )
    )

    status_map = {entry["algorithm"]: entry["status"] for entry in checks}
    missing = [algo for algo in required_algorithms if status_map.get(algo) != "PASS"]

    return {
        "status": "PASS" if not missing else "FAIL",
        "riskMode": risk_mode,
        "requiredAlgorithms": required_algorithms,
        "checks": checks,
        "missingOrInvalidAlgorithms": missing,
    }


def _required_algorithms_for_risk_mode(risk_mode: str) -> list[str]:
    return ["ED25519"] if risk_mode == "STANDARD" else ["ED25519", "ML-DSA"]


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify hybrid signatures for official status")
    parser.add_argument("--payload-file", help="JSON payload file to verify")
    parser.add_argument("--signature-set-file", help="Signature set JSON")
    parser.add_argument("--status-file", help="official_operational_status.json (contains both payload and signatureSet)")
    parser.add_argument("--risk-mode", default=os.environ.get("ETHICBIT_RISK_MODE", "HIGH"))
    parser.add_argument("--ed25519-verify-cmd", default=os.environ.get("ETHICBIT_ED25519_VERIFY_CMD", ""))
    parser.add_argument("--mldsa-verify-cmd", default=os.environ.get("ETHICBIT_MLDSA_VERIFY_CMD", ""))
    parser.add_argument("--require-hybrid", action="store_true", help="Require both Ed25519 and ML-DSA")
    args = parser.parse_args()

    risk_mode = args.risk_mode.upper().strip() or "HIGH"
    if args.require_hybrid:
        required = ["ED25519", "ML-DSA"]
    else:
        required = _required_algorithms_for_risk_mode(risk_mode)

    if args.status_file:
        status_payload = json.loads(Path(args.status_file).read_text(encoding="utf-8"))
        signature_set = status_payload.get("signatureSet")
        payload = dict(status_payload)
        payload.pop("signatureSet", None)
        payload.pop("signatureVerification", None)
        payload.pop("signature", None)
    else:
        if not args.payload_file or not args.signature_set_file:
            raise SystemExit("--status-file or (--payload-file and --signature-set-file) is required")
        payload = json.loads(Path(args.payload_file).read_text(encoding="utf-8"))
        signature_set = json.loads(Path(args.signature_set_file).read_text(encoding="utf-8"))

    if not isinstance(payload, dict):
        raise SystemExit("payload must be a JSON object")
    if not isinstance(signature_set, dict):
        raise SystemExit("signature set must be a JSON object")

    verification = verify_hybrid_signature_set(
        payload,
        signature_set,
        risk_mode=risk_mode,
        ed25519_verify_cmd=args.ed25519_verify_cmd,
        mldsa_verify_cmd=args.mldsa_verify_cmd,
        required_algorithms=required,
    )

    print(json.dumps(verification, indent=2, ensure_ascii=False))
    return 0 if verification.get("status") == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
