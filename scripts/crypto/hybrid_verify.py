#!/usr/bin/env python3
import argparse
import json
import shlex
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from jcs_rfc8785 import canonicalize_bytes


def verify_signature(cmd_parts, payload_path, signature_value):
    final_cmd = [
        part.format(
            payload=str(payload_path),
            signature=signature_value,
        )
        for part in cmd_parts
    ]

    proc = subprocess.run(
        final_cmd,
        check=False,
        capture_output=True,
        text=True,
        timeout=25.0,
    )
    return proc.returncode == 0, (proc.stderr or proc.stdout or "").strip()


def _materialize_payload(payload_or_path: Any) -> tuple[Path, tempfile.TemporaryDirectory | None]:
    if isinstance(payload_or_path, (str, bytes, Path)):
        return Path(payload_or_path), None

    if isinstance(payload_or_path, dict):
        tmp = tempfile.TemporaryDirectory(prefix="ethicbit_verify_payload_")
        payload_path = Path(tmp.name) / "payload.jcs.json"
        payload_path.write_bytes(canonicalize_bytes(payload_or_path))
        return payload_path, tmp

    raise TypeError(f"unsupported payload type: {type(payload_or_path)!r}")


def verify_hybrid_signature_set(
    payload_or_path,
    signature_set: dict,
    *,
    risk_mode: str,
    ed25519_verify_cmd: str,
    mldsa_verify_cmd: str,
    required_algorithms: list[str],
):
    checks = []
    payload_file, tmp_handle = _materialize_payload(payload_or_path)

    try:
        signatures_by_alg = {}
        for entry in signature_set.get("signatures", []):
            alg = entry.get("algorithm")
            if alg:
                signatures_by_alg[alg] = entry

        for alg in required_algorithms:
            cmd_template = ""
            if alg == "ED25519":
                cmd_template = ed25519_verify_cmd
            elif alg == "ML-DSA":
                cmd_template = mldsa_verify_cmd

            result = {
                "algorithm": alg,
                "status": "FAIL",
                "commandConfigured": bool((cmd_template or "").strip()),
                "timeoutSeconds": 25.0,
            }

            entry = signatures_by_alg.get(alg, {})
            sig_value = (entry.get("signature") or "").strip()

            if not cmd_template.strip():
                result["error"] = f"missing verify command for {alg}"
                checks.append(result)
                continue

            if not sig_value:
                result["error"] = "missing signature value"
                checks.append(result)
                continue

            ok, err = verify_signature(
                shlex.split(cmd_template),
                payload_file,
                sig_value,
            )

            if ok:
                result["status"] = "PASS"
            else:
                result["error"] = err or "FAIL"

            checks.append(result)

        missing = [c["algorithm"] for c in checks if c["status"] != "PASS"]

        verification = {
            "status": "PASS" if not missing else "FAIL",
            "riskMode": risk_mode,
            "requiredAlgorithms": required_algorithms,
            "checks": checks,
        }
        if missing:
            verification["missingOrInvalidAlgorithms"] = missing

        return verification
    finally:
        if tmp_handle is not None:
            tmp_handle.cleanup()


def main():
    parser = argparse.ArgumentParser(description="Verify JSON payload with hybrid signature set")
    parser.add_argument("--payload", required=True, help="Input JSON payload")
    parser.add_argument("--signature-set", required=True, help="Input signature set JSON")
    parser.add_argument("--risk-mode", choices=["STANDARD", "HIGH", "GOV"], default="HIGH")
    parser.add_argument("--ed25519-verify-cmd", default="")
    parser.add_argument("--mldsa-verify-cmd", default="")
    args = parser.parse_args()

    sig_set = json.loads(Path(args.signature_set).read_text(encoding="utf-8"))
    required = ["ED25519"] if args.risk_mode == "STANDARD" else ["ED25519", "ML-DSA"]

    verification = verify_hybrid_signature_set(
        args.payload,
        sig_set,
        risk_mode=args.risk_mode,
        ed25519_verify_cmd=args.ed25519_verify_cmd,
        mldsa_verify_cmd=args.mldsa_verify_cmd,
        required_algorithms=required,
    )

    print(json.dumps(verification, indent=2, ensure_ascii=False))
    return 0 if verification.get("status") == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
