#!/usr/bin/env python3
import argparse
import hashlib
import json
import shlex
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from jcs_rfc8785 import canonicalize_bytes


FREEZE_GRADE_LEVELS = {"freeze_grade", "sovereign_release"}
TRUSTED_KEY_SOURCES = {
    "trusted_secrets",
    "trusted_remote_provider",
    "remote_non_exportable",
    "trusted_hsm_kms",
    "hsm_kms",
}


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def _as_bool(value: Any, *, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"1", "true", "yes", "y", "on"}:
            return True
        if normalized in {"0", "false", "no", "n", "off"}:
            return False
    return default


def _normalize_key_source(value: Any) -> str:
    source = str(value or "").strip().lower()
    if not source:
        return "unknown"
    if source in {"trusted", "trusted_secret", "trusted_secrets", "secrets"}:
        return "trusted_secrets"
    if source in {
        "trusted_remote_provider",
        "remote_signing_provider",
        "remote_non_exportable",
        "remote_hsm",
        "hsm",
        "hsm_kms",
        "kms",
        "trusted_hsm_kms",
    }:
        if source in {"hsm", "kms"}:
            return "hsm_kms"
        return source
    if source in {"ephemeral", "ephemeral_runner", "runner_ephemeral"}:
        return "ephemeral_runner"
    return source


def _is_native_mldsa(mode: str) -> bool:
    return mode in {"native", "native_mldsa"}


def _is_trusted_source(source: str) -> bool:
    return source in TRUSTED_KEY_SOURCES


def _derive_ephemeral_from_sources(ed25519_key_source: str, mldsa_key_source: str) -> bool:
    return "ephemeral" in ed25519_key_source or "ephemeral" in mldsa_key_source


def _materialize_payload(payload_or_path: Any) -> tuple[Path, tempfile.TemporaryDirectory | None]:
    if isinstance(payload_or_path, (str, bytes, Path)):
        return Path(payload_or_path), None

    if isinstance(payload_or_path, dict):
        tmp = tempfile.TemporaryDirectory(prefix="ethicbit_verify_payload_")
        payload_path = Path(tmp.name) / "payload.jcs.json"
        payload_path.write_bytes(canonicalize_bytes(payload_or_path))
        return payload_path, tmp

    raise TypeError(f"unsupported payload type: {type(payload_or_path)!r}")


def verify_signature(cmd_parts: list[str], payload_path: Path, signature_value: str) -> tuple[bool, str]:
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


def validate_signature_set_semantics(signature_set: dict[str, Any]) -> list[str]:
    errors: list[str] = []

    truth = signature_set.get("hybridCryptoTruth")
    if not isinstance(truth, dict):
        return ["Missing hybridCryptoTruth in signature set"]

    policy = signature_set.get("verificationPolicy")
    if not isinstance(policy, dict):
        return ["Missing verificationPolicy in signature set"]

    claim_level = str(policy.get("claimLevel") or truth.get("claim_level") or "ci_grade")
    require_native = _as_bool(
        policy.get("requireNativeHybrid", truth.get("require_native_hybrid")),
        default=False,
    )
    mode = str(truth.get("hybrid_claim_mode") or truth.get("hybridClaimMode") or "unknown")
    ed25519_key_source = _normalize_key_source(
        truth.get("ed25519_key_source") or truth.get("ed25519KeySource") or "unknown"
    )
    mldsa_key_source = _normalize_key_source(
        truth.get("mldsa_key_source") or truth.get("mldsaKeySource") or "unknown"
    )
    mldsa_effective_mode = str(
        truth.get("mldsa_effective_mode")
        or truth.get("mldsaEffectiveMode")
        or truth.get("mldsa_mode")
        or truth.get("mldsaMode")
        or "unknown"
    ).lower()
    ephemeral = _as_bool(truth.get("ephemeral_keys_used"), default=False)
    runner_supports_mldsa = _as_bool(truth.get("runner_supports_mldsa"), default=False)
    eligible = _as_bool(truth.get("eligible_for_sovereign_release"), default=False)
    derived_ephemeral = _derive_ephemeral_from_sources(ed25519_key_source, mldsa_key_source)

    if ephemeral != derived_ephemeral:
        errors.append(
            "Verification failed: ephemeral_keys_used does not match declared key sources"
        )

    if require_native and mode != "native_hybrid":
        errors.append(
            f"Verification failed: requireNativeHybrid=true but hybrid_claim_mode={mode}"
        )

    if require_native and not _is_native_mldsa(mldsa_effective_mode):
        errors.append(
            "Verification failed: requireNativeHybrid=true but mldsa_effective_mode is not native"
        )
    if mode == "native_hybrid" and not _is_native_mldsa(mldsa_effective_mode):
        errors.append(
            "Verification failed: native_hybrid claim with non-native ML-DSA mode"
        )

    eligible_by_truth = (
        not ephemeral
        and mode == "native_hybrid"
        and _is_trusted_source(ed25519_key_source)
        and _is_trusted_source(mldsa_key_source)
        and _is_native_mldsa(mldsa_effective_mode)
        and runner_supports_mldsa
    )
    if eligible and not eligible_by_truth:
        errors.append(
            "Verification failed: eligible_for_sovereign_release=true but truth requirements are not met"
        )

    if claim_level in FREEZE_GRADE_LEVELS:
        if ephemeral:
            errors.append(
                "Verification failed: ephemeral keys not allowed for freeze/release-grade claim"
            )
        if not _is_trusted_source(ed25519_key_source) or not _is_trusted_source(mldsa_key_source):
            errors.append(
                "Verification failed: trusted key sources required for freeze/release-grade claim"
            )
        if mode != "native_hybrid":
            errors.append(
                "Verification failed: freeze/release-grade claim requires native_hybrid mode"
            )
        if not _is_native_mldsa(mldsa_effective_mode):
            errors.append(
                "Verification failed: freeze/release-grade claim requires native ML-DSA mode"
            )
        if not eligible:
            errors.append(
                "Verification failed: signature set not eligible for freeze/release-grade claim"
            )

    mldsa_entry = None
    for sig in signature_set.get("signatures", []):
        if isinstance(sig, dict) and sig.get("algorithm") == "ML-DSA":
            mldsa_entry = sig
            break

    require_mldsa_signature = require_native or claim_level in FREEZE_GRADE_LEVELS
    if require_mldsa_signature and not isinstance(mldsa_entry, dict):
        errors.append(
            "Verification failed: ML-DSA signature is required by claim policy"
        )

    if isinstance(mldsa_entry, dict):
        entry_mode = str(mldsa_entry.get("effectiveMode", "")).lower().strip()
        if entry_mode and mldsa_effective_mode and entry_mode != mldsa_effective_mode:
            errors.append(
                f"Verification failed: ML-DSA effectiveMode mismatch entry={entry_mode} truth={mldsa_effective_mode}"
            )

    return errors


def verify_hybrid_signature_set(
    payload_or_path,
    signature_set: dict,
    *,
    risk_mode: str,
    ed25519_verify_cmd: str,
    mldsa_verify_cmd: str,
    required_algorithms: list[str],
):
    checks: list[dict[str, Any]] = []
    payload_file, tmp_handle = _materialize_payload(payload_or_path)

    try:
        semantic_errors = validate_signature_set_semantics(signature_set)
        policy = signature_set.get("verificationPolicy") if isinstance(signature_set, dict) else {}
        truth = signature_set.get("hybridCryptoTruth") if isinstance(signature_set, dict) else {}
        claim_level = ""
        if isinstance(policy, dict):
            claim_level = str(policy.get("claimLevel") or "")
        if not claim_level and isinstance(truth, dict):
            claim_level = str(truth.get("claim_level") or "")
        require_native = False
        if isinstance(policy, dict):
            require_native = _as_bool(policy.get("requireNativeHybrid"), default=False)
        if not require_native and isinstance(truth, dict):
            require_native = _as_bool(truth.get("require_native_hybrid"), default=False)

        required_for_verification: list[str] = list(required_algorithms)
        if require_native or claim_level in FREEZE_GRADE_LEVELS:
            if "ML-DSA" not in required_for_verification:
                required_for_verification.append("ML-DSA")

        expected_sha = signature_set.get("payload", {}).get("sha256")
        if isinstance(expected_sha, str) and expected_sha:
            actual_sha = sha256_file(payload_file)
            if expected_sha != actual_sha:
                semantic_errors.append(
                    f"Payload hash mismatch: expected={expected_sha} actual={actual_sha}"
                )

        signatures_by_alg: dict[str, dict[str, Any]] = {}
        for entry in signature_set.get("signatures", []):
            if isinstance(entry, dict):
                alg = entry.get("algorithm")
                if isinstance(alg, str) and alg:
                    signatures_by_alg[alg] = entry

        for alg in required_for_verification:
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
            sig_value = (entry.get("signature") or "").strip() if isinstance(entry, dict) else ""

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
            "status": "PASS" if not missing and not semantic_errors else "FAIL",
            "riskMode": risk_mode,
            "requiredAlgorithms": required_for_verification,
            "semanticStatus": "PASS" if not semantic_errors else "FAIL",
            "checks": checks,
        }
        if semantic_errors:
            verification["semanticErrors"] = semantic_errors
        if missing:
            verification["missingOrInvalidAlgorithms"] = missing

        return verification
    finally:
        if tmp_handle is not None:
            tmp_handle.cleanup()


def main() -> int:
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
