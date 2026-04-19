#!/usr/bin/env python3
import argparse
import hashlib
import json
import os
import shlex
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from jcs_rfc8785 import canonicalize_bytes


def now_utc():
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sign_one(*, algorithm: str, command_template: str, key_id: str, payload_bytes: bytes):
    result = {
        "algorithm": algorithm,
        "keyId": key_id,
        "status": "FAIL",
        "signature": "",
        "signedAt": now_utc(),
        "commandConfigured": bool((command_template or "").strip()),
        "timeoutSeconds": 25.0,
    }

    if not (command_template or "").strip():
        result["error"] = f"missing signer command for {algorithm}"
        return result

    with tempfile.TemporaryDirectory(prefix=f"ethicbit_sign_{algorithm.lower().replace('-', '_')}_") as tmp:
        payload_path = Path(tmp) / "payload.jcs.json"
        payload_path.write_bytes(payload_bytes)

        cmd = shlex.split(
            command_template.format(
                payload=str(payload_path),
                signature="",
                algorithm=algorithm,
                key_id=key_id,
            )
        )

        try:
            proc = subprocess.run(
                cmd,
                check=False,
                capture_output=True,
                text=True,
                timeout=25.0,
            )
        except subprocess.TimeoutExpired:
            result["error"] = "signer command timeout after 25.0s"
            return result

        if proc.returncode != 0:
            result["error"] = (proc.stderr or proc.stdout or "signer command failed").strip()
            return result

        sig = (proc.stdout or "").strip()
        if not sig:
            result["error"] = "empty signature output"
            return result

        result["signature"] = sig
        result["status"] = "PASS"
        return result


def build_hybrid_signature_set(
    payload: dict,
    *,
    policy_version: str,
    run_context: dict,
    risk_mode: str,
    ed25519_sign_cmd: str,
    mldsa_sign_cmd: str,
    ed25519_key_id: str,
    mldsa_key_id: str,
    required_algorithms: list[str],
    crypto_mode: dict | None = None,
):
    payload_bytes = canonicalize_bytes(payload)

    signatures = []

    if "ED25519" in required_algorithms:
        signatures.append(
            sign_one(
                algorithm="ED25519",
                command_template=ed25519_sign_cmd,
                key_id=ed25519_key_id,
                payload_bytes=payload_bytes,
            )
        )

    if "ML-DSA" in required_algorithms:
        signatures.append(
            sign_one(
                algorithm="ML-DSA",
                command_template=mldsa_sign_cmd,
                key_id=mldsa_key_id,
                payload_bytes=payload_bytes,
            )
        )

    status_by_algo = {s["algorithm"]: s["status"] for s in signatures}
    missing = [alg for alg in required_algorithms if status_by_algo.get(alg) != "PASS"]

    summary = {
        "status": "PASS" if not missing else "FAIL",
        "policyVersion": policy_version,
        "riskMode": risk_mode,
        "runContext": run_context,
        "requiredAlgorithms": required_algorithms,
        "payloadHash": sha256_hex(payload_bytes),
        "signatures": signatures,
    }
    if isinstance(crypto_mode, dict) and crypto_mode:
        summary["cryptoMode"] = crypto_mode
    if missing:
        summary["missingOrInvalidAlgorithms"] = missing

    return summary, payload_bytes


def main():
    parser = argparse.ArgumentParser(description="Sign JSON payload with hybrid signer hooks")
    parser.add_argument("payload", help="Input JSON payload")
    parser.add_argument("--output", required=True, help="Output signature set JSON")
    parser.add_argument("--risk-mode", choices=["STANDARD", "HIGH", "GOV"], default="HIGH")
    parser.add_argument("--policy-version", default="official-operational-status-policy.v2.0.0")
    parser.add_argument("--ed25519-sign-cmd", default=os.environ.get("ETHICBIT_ED25519_SIGN_CMD", ""))
    parser.add_argument("--mldsa-sign-cmd", default=os.environ.get("ETHICBIT_MLDSA_SIGN_CMD", ""))
    parser.add_argument("--ed25519-key-id", default=os.environ.get("ETHICBIT_ED25519_KEY_ID", "ED25519_UNSET"))
    parser.add_argument("--mldsa-key-id", default=os.environ.get("ETHICBIT_MLDSA_KEY_ID", "MLDSA_UNSET"))
    args = parser.parse_args()

    payload = json.loads(Path(args.payload).read_text(encoding="utf-8"))
    required = ["ED25519"] if args.risk_mode == "STANDARD" else ["ED25519", "ML-DSA"]
    crypto_mode = {
        "effectiveMode": os.environ.get("ETHICBIT_CRYPTO_MODE_EFFECTIVE", "unknown"),
        "mldsaMode": os.environ.get("ETHICBIT_MLDSA_MODE", "unknown"),
        "keyProvenanceMode": os.environ.get("ETHICBIT_KEY_PROVENANCE_MODE", "unknown"),
        "claimTier": os.environ.get("ETHICBIT_CRYPTO_CLAIM_TIER", "unspecified"),
    }
    audit_require_hybrid = os.environ.get("ETHICBIT_AUDIT_REQUIRE_HYBRID", "").strip()
    if audit_require_hybrid:
        crypto_mode["auditRequireHybrid"] = audit_require_hybrid
    release_class = os.environ.get("ETHICBIT_RELEASE_CLASS", "").strip()
    if release_class:
        crypto_mode["releaseClass"] = release_class

    signature_set, _ = build_hybrid_signature_set(
        payload,
        policy_version=args.policy_version,
        run_context={"runId": "CLI", "releaseId": "CLI", "verificationEpoch": "CLI"},
        risk_mode=args.risk_mode,
        ed25519_sign_cmd=args.ed25519_sign_cmd,
        mldsa_sign_cmd=args.mldsa_sign_cmd,
        ed25519_key_id=args.ed25519_key_id,
        mldsa_key_id=args.mldsa_key_id,
        required_algorithms=required,
        crypto_mode=crypto_mode,
    )

    Path(args.output).write_text(json.dumps(signature_set, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(signature_set["status"])
    return 0 if signature_set["status"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
