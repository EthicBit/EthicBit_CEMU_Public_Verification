#!/usr/bin/env python3
import argparse
import hashlib
import json
import os
import shlex
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from jcs_rfc8785 import canonicalize_bytes


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _render_command(template: str, *, payload: Path, signature: str, key_id: str, algorithm: str) -> list[str]:
    rendered = template.format(
        payload=str(payload),
        signature=signature,
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
    command_template: str,
    key_id: str,
    signature_value: str,
    payload_bytes: bytes,
) -> dict[str, Any]:
    result: dict[str, Any] = {
        "algorithm": algorithm,
        "status": "FAIL",
        "commandConfigured": bool(command_template.strip()),
    }

    if not command_template.strip():
        result["error"] = f"missing verify command for {algorithm}"
        return result

    signature_value = (signature_value or "").strip()
    if not signature_value:
        result["error"] = "missing signature value"
        return result

    timeout_seconds = _command_timeout_seconds()
    result["timeoutSeconds"] = timeout_seconds

    with tempfile.TemporaryDirectory(prefix=f"ethicbit_verify_{algorithm.lower()}_") as tmp:
        payload_path = Path(tmp) / "payload.jcs.json"
        payload_path.write_bytes(payload_bytes)

        cmd = _render_command(
            command_template,
            payload=payload_path,
            signature=signature_value,
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

    signatures = signature_set.get("signatures", [])
    by_algo = {}
    for entry in signatures:
        algo = entry.get("algorithm")
        if algo:
            by_algo[algo] = entry

    ed_entry = by_algo.get("ED25519", {})
    ml_entry = by_algo.get("ML-DSA", {})

    checks = [
        _verify_one(
            algorithm="ED25519",
            command_template=ed25519_verify_cmd,
            key_id=ed_entry.get("keyId", "ED25519_UNSET"),
            signature_value=ed_entry.get("signature", ""),
            payload_bytes=payload_bytes,
        ),
        _verify_one(
            algorithm="ML-DSA",
            command_template=mldsa_verify_cmd,
            key_id=ml_entry.get("keyId", "MLDSA_UNSET"),
            signature_value=ml_entry.get("signature", ""),
            payload_bytes=payload_bytes,
        ),
    ]

    status_by_algo = {entry["algorithm"]: entry["status"] for entry in checks}
    missing = [algo for algo in required_algorithms if status_by_algo.get(algo) != "PASS"]
    status = "PASS" if not missing else "FAIL"

    summary: dict[str, Any] = {
        "status": status,
        "riskMode": risk_mode,
        "requiredAlgorithms": required_algorithms,
        "checks": checks,
    }
    if missing:
        summary["missingOrInvalidAlgorithms"] = missing
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify JSON payload with hybrid verifier hooks")
    parser.add_argument("--payload-file", help="Input JSON payload file")
    parser.add_argument("--signature-set-file", help="Signature set JSON file")
    parser.add_argument("--status-file", help="Official operational status JSON file")
    parser.add_argument("--risk-mode", default="HIGH")
    parser.add_argument("--ed25519-verify-cmd", default=os.environ.get("ETHICBIT_ED25519_VERIFY_CMD", ""))
    parser.add_argument("--mldsa-verify-cmd", default=os.environ.get("ETHICBIT_MLDSA_VERIFY_CMD", ""))
    args = parser.parse_args()

    if args.status_file:
        status_doc = json.loads(Path(args.status_file).read_text(encoding="utf-8"))
        payload = {k: v for k, v in status_doc.items() if k not in ("signature", "signatureSet", "signatureVerification")}
        signature_set = status_doc.get("signatureSet", {})
    elif args.payload_file and args.signature_set_file:
        payload = json.loads(Path(args.payload_file).read_text(encoding="utf-8"))
        signature_set = json.loads(Path(args.signature_set_file).read_text(encoding="utf-8"))
    else:
        raise SystemExit("--status-file or (--payload-file and --signature-set-file) is required")

    risk_mode = (args.risk_mode or "HIGH").upper().strip()
    required = ["ED25519"] if risk_mode == "STANDARD" else ["ED25519", "ML-DSA"]

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
