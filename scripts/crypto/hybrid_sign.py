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
from typing import Any

from jcs_rfc8785 import canonicalize_bytes


FREEZE_GRADE_LEVELS = {"freeze_grade", "sovereign_release"}
NATIVE_MLDSA_MODES = {"native", "native_mldsa"}
TRUSTED_KEY_SOURCES = {"trusted_secrets"}


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_hex(path.read_bytes())


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


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


def _normalize_mode(value: Any) -> str:
    raw = str(value or "").strip().lower()
    if raw in NATIVE_MLDSA_MODES:
        return "native"
    if raw in {"compatibility_fallback", "compat_fallback", "fallback"}:
        return "compatibility_fallback"
    return raw or "unknown"


def _normalize_key_source(value: Any) -> str:
    source = str(value or "").strip().lower()
    if not source:
        return "unknown"
    if source in {"trusted", "trusted_secret", "trusted_secrets", "secrets"}:
        return "trusted_secrets"
    if source in {"ephemeral", "ephemeral_runner", "runner_ephemeral"}:
        return "ephemeral_runner"
    return source


def _is_native_mldsa(mode: str) -> bool:
    return mode in {"native", "native_mldsa"}


def _is_trusted_source(source: str) -> bool:
    return source in TRUSTED_KEY_SOURCES


def _derive_ephemeral_from_sources(ed25519_key_source: str, mldsa_key_source: str) -> bool:
    return "ephemeral" in ed25519_key_source or "ephemeral" in mldsa_key_source


def _normalize_truth(
    truth: dict[str, Any] | None,
    *,
    claim_level: str,
    require_native_hybrid: bool,
) -> dict[str, Any]:
    raw = truth or {}

    ed25519_key_source = _normalize_key_source(
        raw.get("ed25519_key_source")
        or raw.get("ed25519KeySource")
        or "unknown"
    )
    mldsa_key_source = _normalize_key_source(
        raw.get("mldsa_key_source")
        or raw.get("mldsaKeySource")
        or "unknown"
    )
    mldsa_effective_mode = _normalize_mode(
        raw.get("mldsa_effective_mode")
        or raw.get("mldsaEffectiveMode")
        or raw.get("mldsa_mode")
        or raw.get("mldsaMode")
    )

    hybrid_claim_mode = str(
        raw.get("hybrid_claim_mode")
        or raw.get("hybridClaimMode")
        or ("native_hybrid" if _is_native_mldsa(mldsa_effective_mode) else "compatibility_hybrid")
    )

    ephemeral_keys_used = raw.get("ephemeral_keys_used")
    if ephemeral_keys_used is None:
        ephemeral_keys_used = _derive_ephemeral_from_sources(ed25519_key_source, mldsa_key_source)
    ephemeral_keys_used = _as_bool(ephemeral_keys_used, default=False)

    runner_supports_mldsa = raw.get("runner_supports_mldsa")
    if runner_supports_mldsa is None:
        runner_supports_mldsa = _is_native_mldsa(mldsa_effective_mode)
    runner_supports_mldsa = _as_bool(runner_supports_mldsa, default=False)

    eligible_for_sovereign_release = raw.get("eligible_for_sovereign_release")
    if eligible_for_sovereign_release is None:
        eligible_for_sovereign_release = (
            not ephemeral_keys_used
            and hybrid_claim_mode == "native_hybrid"
            and _is_trusted_source(ed25519_key_source)
            and _is_trusted_source(mldsa_key_source)
            and _is_native_mldsa(mldsa_effective_mode)
            and runner_supports_mldsa
        )
    eligible_for_sovereign_release = _as_bool(eligible_for_sovereign_release, default=False)

    normalized = {
        "ed25519_key_source": ed25519_key_source,
        "mldsa_key_source": mldsa_key_source,
        "mldsa_effective_mode": mldsa_effective_mode,
        "hybrid_claim_mode": hybrid_claim_mode,
        "ephemeral_keys_used": ephemeral_keys_used,
        "runner_supports_mldsa": runner_supports_mldsa,
        "claim_level": claim_level,
        "require_native_hybrid": bool(require_native_hybrid),
        "eligible_for_sovereign_release": eligible_for_sovereign_release,
    }

    key_provenance_mode = raw.get("key_provenance_mode") or raw.get("keyProvenanceMode")
    if key_provenance_mode is not None:
        normalized["key_provenance_mode"] = key_provenance_mode
        normalized["keyProvenanceMode"] = key_provenance_mode

    crypto_claim_tier = raw.get("crypto_claim_tier") or raw.get("claim_tier") or raw.get("claimTier")
    if crypto_claim_tier is not None:
        normalized["crypto_claim_tier"] = crypto_claim_tier
        normalized["claimTier"] = crypto_claim_tier

    release_class = raw.get("release_class") or raw.get("releaseClass")
    if release_class is not None:
        normalized["release_class"] = release_class
        normalized["releaseClass"] = release_class

    # Preserve useful legacy metadata when present.
    for legacy_key in (
        "keyProvenanceMode",
        "claimTier",
        "releaseClass",
        "auditRequireHybrid",
        "ed25519KeyId",
        "mldsaKeyId",
    ):
        if legacy_key in raw:
            normalized[legacy_key] = raw[legacy_key]

    return normalized


def validate_crypto_truth_for_signing(
    truth: dict[str, Any],
    *,
    require_native_hybrid: bool,
    claim_level: str,
) -> None:
    mode = str(truth.get("hybrid_claim_mode", "unknown"))
    mldsa_effective_mode = str(truth.get("mldsa_effective_mode", "unknown"))
    ed25519_key_source = str(truth.get("ed25519_key_source", "unknown"))
    mldsa_key_source = str(truth.get("mldsa_key_source", "unknown"))
    ephemeral = _as_bool(truth.get("ephemeral_keys_used"), default=False)
    runner_supports_mldsa = _as_bool(truth.get("runner_supports_mldsa"), default=False)
    eligible = _as_bool(truth.get("eligible_for_sovereign_release"), default=False)
    derived_ephemeral = _derive_ephemeral_from_sources(ed25519_key_source, mldsa_key_source)

    if ephemeral != derived_ephemeral:
        raise SystemExit(
            "Crypto truth inconsistent: ephemeral_keys_used does not match key sources"
        )

    if require_native_hybrid and mode != "native_hybrid":
        raise SystemExit(f"Native hybrid required for signing, but hybrid_claim_mode={mode}")
    if require_native_hybrid and not _is_native_mldsa(mldsa_effective_mode):
        raise SystemExit(
            "Native hybrid required for signing, but mldsa_effective_mode is not native"
        )
    if mode == "native_hybrid" and not _is_native_mldsa(mldsa_effective_mode):
        raise SystemExit(
            "Crypto truth inconsistent: native_hybrid claim with non-native ML-DSA mode"
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
        raise SystemExit(
            "Crypto truth inconsistent: eligible_for_sovereign_release=true but requirements are not met"
        )

    if claim_level in FREEZE_GRADE_LEVELS:
        if ephemeral:
            raise SystemExit("Ephemeral keys are not allowed for freeze/release-grade signature sets")
        if not _is_trusted_source(ed25519_key_source) or not _is_trusted_source(mldsa_key_source):
            raise SystemExit("Trusted key sources are required for freeze/release-grade signature sets")
        if mode != "native_hybrid":
            raise SystemExit("Native hybrid claim is required for freeze/release-grade signature sets")
        if not _is_native_mldsa(mldsa_effective_mode):
            raise SystemExit("Native ML-DSA mode is required for freeze/release-grade signature sets")
        if not eligible:
            raise SystemExit("Signature set is not eligible for freeze/release-grade claim")


def run_sign_cmd(cmd_template: str, *, payload_path: Path) -> tuple[int, str, str]:
    cmd = cmd_template.format(
        payload=str(payload_path),
        signature="",
        algorithm="",
        key_id="",
    )
    proc = subprocess.run(
        shlex.split(cmd),
        check=False,
        capture_output=True,
        text=True,
        timeout=25.0,
    )
    return proc.returncode, (proc.stdout or "").strip(), (proc.stderr or "").strip()


def _build_signature_entry(
    *,
    algorithm: str,
    key_id: str,
    cmd_template: str,
    payload_path: Path,
    mldsa_effective_mode: str,
) -> dict[str, Any]:
    result = {
        "algorithm": algorithm,
        "keyId": key_id,
        "status": "FAIL",
        "signature": "",
        "signedAt": now_utc(),
        "commandConfigured": bool((cmd_template or "").strip()),
        "timeoutSeconds": 25.0,
    }

    if algorithm == "ML-DSA":
        result["effectiveMode"] = mldsa_effective_mode

    if not (cmd_template or "").strip():
        result["error"] = f"missing signer command for {algorithm}"
        return result

    code, stdout_text, stderr_text = run_sign_cmd(cmd_template, payload_path=payload_path)
    if code != 0:
        result["error"] = stderr_text or stdout_text or "signer command failed"
        return result
    if not stdout_text:
        result["error"] = "empty signature output"
        return result

    result["signature"] = stdout_text
    result["status"] = "PASS"
    return result


def _build_payload_file(
    payload_bytes: bytes,
    *,
    payload_canonical_path: str | None,
) -> tuple[Path, tempfile.TemporaryDirectory | None]:
    if payload_canonical_path:
        p = Path(payload_canonical_path)
        if p.exists():
            return p, None

    tmp = tempfile.TemporaryDirectory(prefix="ethicbit_hybrid_sign_")
    payload_path = Path(tmp.name) / "payload.jcs.json"
    payload_path.write_bytes(payload_bytes)
    return payload_path, tmp


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
    crypto_truth: dict | None = None,
    claim_level: str = "ci_grade",
    require_native_hybrid: bool = False,
    payload_source_path: str | None = None,
    payload_canonical_path: str | None = None,
):
    payload_bytes = canonicalize_bytes(payload)
    truth_input = crypto_truth if isinstance(crypto_truth, dict) else crypto_mode
    normalized_truth = _normalize_truth(
        truth_input if isinstance(truth_input, dict) else {},
        claim_level=claim_level,
        require_native_hybrid=require_native_hybrid,
    )
    validate_crypto_truth_for_signing(
        normalized_truth,
        require_native_hybrid=require_native_hybrid,
        claim_level=claim_level,
    )
    required_set = set(required_algorithms)
    if require_native_hybrid and "ML-DSA" not in required_set:
        raise SystemExit(
            "Invalid signing configuration: requireNativeHybrid=true requires ML-DSA signature"
        )
    if claim_level in FREEZE_GRADE_LEVELS and "ML-DSA" not in required_set:
        raise SystemExit(
            "Invalid signing configuration: freeze/release-grade claim requires ML-DSA signature"
        )

    payload_path, tmp_handle = _build_payload_file(
        payload_bytes,
        payload_canonical_path=payload_canonical_path,
    )

    try:
        signatures: list[dict[str, Any]] = []

        if "ED25519" in required_algorithms:
            signatures.append(
                _build_signature_entry(
                    algorithm="ED25519",
                    key_id=ed25519_key_id,
                    cmd_template=ed25519_sign_cmd,
                    payload_path=payload_path,
                    mldsa_effective_mode=normalized_truth["mldsa_effective_mode"],
                )
            )

        if "ML-DSA" in required_algorithms:
            signatures.append(
                _build_signature_entry(
                    algorithm="ML-DSA",
                    key_id=mldsa_key_id,
                    cmd_template=mldsa_sign_cmd,
                    payload_path=payload_path,
                    mldsa_effective_mode=normalized_truth["mldsa_effective_mode"],
                )
            )

        status_by_algo = {s["algorithm"]: s["status"] for s in signatures}
        missing = [alg for alg in required_algorithms if status_by_algo.get(alg) != "PASS"]

        summary = {
            "artifactType": "hybrid_signature_set",
            "schemaVersion": "2.0.0",
            "status": "PASS" if not missing else "FAIL",
            "policyVersion": policy_version,
            "riskMode": risk_mode,
            "runContext": run_context,
            "requiredAlgorithms": required_algorithms,
            "payloadHash": sha256_hex(payload_bytes),
            "payload": {
                "path": str(payload_path),
                "sha256": sha256_hex(payload_bytes),
                "sourcePath": str(payload_source_path or ""),
            },
            "hybridCryptoTruth": normalized_truth,
            "verificationPolicy": {
                "claimLevel": claim_level,
                "requireNativeHybrid": bool(require_native_hybrid),
            },
            "signatures": signatures,
            # Backward-compatible mirror for existing consumers.
            "cryptoMode": {
                "effectiveMode": "native_hybrid"
                if normalized_truth["hybrid_claim_mode"] == "native_hybrid"
                else "compatibility_fallback",
                "mldsaMode": normalized_truth["mldsa_effective_mode"],
                "mldsaEffectiveMode": normalized_truth["mldsa_effective_mode"],
                "ed25519KeySource": normalized_truth["ed25519_key_source"],
                "mldsaKeySource": normalized_truth["mldsa_key_source"],
                "hybridClaimMode": normalized_truth["hybrid_claim_mode"],
                "keyProvenanceMode": normalized_truth.get("keyProvenanceMode", "unknown"),
                "claimTier": normalized_truth.get("claimTier", "unspecified"),
            },
        }

        if missing:
            summary["missingOrInvalidAlgorithms"] = missing

        return summary, payload_bytes
    finally:
        if tmp_handle is not None:
            tmp_handle.cleanup()


def _resolve_cli_truth(args: argparse.Namespace) -> dict[str, Any]:
    if args.crypto_truth_json:
        truth_path = Path(args.crypto_truth_json).resolve()
        if not truth_path.exists():
            raise SystemExit(f"Missing crypto truth file: {truth_path}")
        return load_json(truth_path)

    return {
        "ed25519_key_source": os.environ.get("ETHICBIT_ED25519_KEY_SOURCE", "unknown"),
        "mldsa_key_source": os.environ.get("ETHICBIT_MLDSA_KEY_SOURCE", "unknown"),
        "mldsa_effective_mode": os.environ.get(
            "ETHICBIT_MLDSA_EFFECTIVE_MODE",
            os.environ.get("ETHICBIT_MLDSA_MODE", "unknown"),
        ),
        "hybrid_claim_mode": os.environ.get("ETHICBIT_HYBRID_CLAIM_MODE", "unknown"),
        "key_provenance_mode": os.environ.get("ETHICBIT_KEY_PROVENANCE_MODE", "unknown"),
        "crypto_claim_tier": os.environ.get("ETHICBIT_CRYPTO_CLAIM_TIER", "unspecified"),
        "release_class": os.environ.get("ETHICBIT_RELEASE_CLASS", "branch_ci"),
        "ephemeral_keys_used": _as_bool(os.environ.get("ETHICBIT_EPHEMERAL_KEYS_USED"), default=False),
        "runner_supports_mldsa": _as_bool(os.environ.get("ETHICBIT_RUNNER_SUPPORTS_MLDSA"), default=False),
        "eligible_for_sovereign_release": _as_bool(
            os.environ.get("ETHICBIT_ELIGIBLE_FOR_SOVEREIGN_RELEASE"),
            default=False,
        ),
    }


def _resolve_canonical_path(payload_path: Path) -> str | None:
    candidates = [
        payload_path.with_suffix(".jcs.json"),
        payload_path.with_suffix(".verify.jcs.json"),
    ]
    for candidate in candidates:
        if candidate.exists():
            return str(candidate)
    return None


def main() -> int:
    parser = argparse.ArgumentParser(description="Sign JSON payload with hybrid signer hooks")
    parser.add_argument("payload", help="Input JSON payload")
    parser.add_argument("--output", required=True, help="Output signature set JSON")
    parser.add_argument("--risk-mode", choices=["STANDARD", "HIGH", "GOV"], default="HIGH")
    parser.add_argument("--policy-version", default="official-operational-status-policy.v2.0.0")
    parser.add_argument("--ed25519-sign-cmd", default=os.environ.get("ETHICBIT_ED25519_SIGN_CMD", ""))
    parser.add_argument("--mldsa-sign-cmd", default=os.environ.get("ETHICBIT_MLDSA_SIGN_CMD", ""))
    parser.add_argument("--ed25519-key-id", default=os.environ.get("ETHICBIT_ED25519_KEY_ID", "ED25519_UNSET"))
    parser.add_argument("--mldsa-key-id", default=os.environ.get("ETHICBIT_MLDSA_KEY_ID", "MLDSA_UNSET"))
    parser.add_argument("--crypto-truth-json", default="")
    parser.add_argument("--claim-level", default=os.environ.get("ETHICBIT_CLAIM_LEVEL", "ci_grade"))
    parser.add_argument(
        "--require-native-hybrid",
        action="store_true",
        default=_as_bool(os.environ.get("ETHICBIT_REQUIRE_NATIVE_HYBRID"), default=False),
        help="Require native hybrid mode in crypto truth",
    )
    args = parser.parse_args()

    payload_path = Path(args.payload).resolve()
    if not payload_path.exists():
        raise SystemExit(f"Missing payload: {payload_path}")

    payload = load_json(payload_path)
    required = ["ED25519"] if args.risk_mode == "STANDARD" else ["ED25519", "ML-DSA"]
    if args.require_native_hybrid or args.claim_level in FREEZE_GRADE_LEVELS:
        if "ML-DSA" not in required:
            required.append("ML-DSA")
    crypto_truth = _resolve_cli_truth(args)

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
        crypto_truth=crypto_truth,
        claim_level=args.claim_level,
        require_native_hybrid=bool(args.require_native_hybrid),
        payload_source_path=str(payload_path),
        payload_canonical_path=_resolve_canonical_path(payload_path),
    )

    output_path = Path(args.output).resolve()
    output_path.write_text(json.dumps(signature_set, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(str(output_path))
    print(signature_set["status"])
    return 0 if signature_set["status"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
