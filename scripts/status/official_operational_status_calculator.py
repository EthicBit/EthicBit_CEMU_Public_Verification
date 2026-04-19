#!/usr/bin/env python3
"""
Official Operational Status Calculator
EthicBit / CEMU v3.7.0+

Fail-closed cryptography controls:
- Canonical payload (RFC 8785-style JCS)
- Hybrid signatures (Ed25519 + ML-DSA) using external signer hooks
- Hybrid verification required by risk mode
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shlex
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PASS_TOKENS = {
    "PASS",
    "PASSED",
    "OK",
    "SUCCESS",
    "READY",
    "ACTIVE_CANONICAL",
    "READY_FOR_CONTROLLED_PRODUCTION",
    "READY_FOR_CONTROLLED_PRODUCTION",
    "CONTROLLED_PRODUCTION_ACTIVE",
    "ANCHOR_HARDENING_ENABLED",
    "TRUE",
}

FAIL_TOKENS = {
    "FAIL",
    "FAILED",
    "ERROR",
    "NOT_VERIFIED",
    "BLOCKED",
    "DEGRADED",
    "INVALID",
    "PARTIAL_PENDING",
    "PENDING",
    "RETRY_REQUIRED",
    "FALSE",
}

PLACEHOLDER_TOKENS = ("PENDING", "PON_AQUI", "PLACEHOLDER", "TODO", "TBD", "EMPTY")
DEFAULT_POLICY_VERSION = "official-operational-status-policy.v2.0.0"
DEFAULT_RISK_MODE = "HIGH"
DEFAULT_OPERATING_MODE = "SOVEREIGN_INTERNAL"
DEFAULT_ED25519_SIGNER = "assurance/signers/ed25519_sign.sh"
DEFAULT_MLDSA_SIGNER = "assurance/signers/mldsa_sign.sh"
DEFAULT_ED25519_VERIFIER = "assurance/signers/ed25519_verify.sh"
DEFAULT_MLDSA_VERIFIER = "assurance/signers/mldsa_verify.sh"


def fail(message: str) -> None:
    raise SystemExit(f"OFFICIAL_STATUS_INVALID: {message}")


def now_utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _load_crypto_modules() -> tuple[Any, Any, Any]:
    crypto_dir = Path(__file__).resolve().parents[1] / "crypto"
    if str(crypto_dir) not in sys.path:
        sys.path.insert(0, str(crypto_dir))
    try:
        from hybrid_sign import build_hybrid_signature_set
        from hybrid_verify import verify_hybrid_signature_set
        from jcs_rfc8785 import canonicalize_bytes
    except Exception as exc:
        fail(f"unable to import crypto modules from {crypto_dir}: {exc}")
    return build_hybrid_signature_set, verify_hybrid_signature_set, canonicalize_bytes


def canonical_json_bytes(payload: dict[str, Any]) -> bytes:
    _, _, canonicalize_bytes = _load_crypto_modules()
    return canonicalize_bytes(payload)


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        while True:
            chunk = handle.read(65536)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def read_json(path: Path, *, required: bool) -> Any:
    if not path.exists():
        if required:
            fail(f"missing required file: {path}")
        return None
    try:
        with open(path, "r", encoding="utf-8") as handle:
            return json.load(handle)
    except json.JSONDecodeError as exc:
        fail(f"invalid JSON at {path}: {exc}")
    except OSError as exc:
        fail(f"unable to read {path}: {exc}")


def classify_scalar(value: Any) -> str:
    if isinstance(value, bool):
        return "PASS" if value else "FAIL"

    if not isinstance(value, str):
        return "UNKNOWN"

    normalized = value.strip().upper()
    if not normalized:
        return "UNKNOWN"
    if normalized in PASS_TOKENS or normalized.startswith("PASS"):
        return "PASS"
    if normalized in FAIL_TOKENS:
        return "FAIL"
    if "FAIL" in normalized or "NOT_VERIFIED" in normalized:
        return "FAIL"
    if "PENDING" in normalized or "PARTIAL" in normalized:
        return "FAIL"
    return "UNKNOWN"


def classify_mapping(values: dict[str, Any]) -> str:
    if not values:
        return "UNKNOWN"

    saw_pass = False
    for value in values.values():
        status = classify_scalar(value)
        if status == "FAIL":
            return "FAIL"
        if status == "PASS":
            saw_pass = True
    return "PASS" if saw_pass else "UNKNOWN"


def derive_gate_status(report: dict[str, Any]) -> tuple[str, str]:
    for key in ("status", "overall_status", "overallStatus", "result"):
        status = classify_scalar(report.get(key))
        if status in {"PASS", "FAIL"}:
            return status, key

    candidates: list[tuple[str, str]] = []

    verified_state = report.get("verifiedState")
    if isinstance(verified_state, dict):
        candidates.append((classify_mapping(verified_state), "verifiedState"))

    gates = report.get("gates")
    if isinstance(gates, dict):
        candidates.append((classify_mapping(gates), "gates"))

    for status, source in candidates:
        if status == "FAIL":
            return "FAIL", source
    for status, source in candidates:
        if status == "PASS":
            return "PASS", source
    return "UNKNOWN", "cannot_derive"


def derive_live_status(report: dict[str, Any]) -> tuple[str, str]:
    for key in ("overall_status", "overallStatus", "status", "result"):
        status = classify_scalar(report.get(key))
        if status in {"PASS", "FAIL"}:
            return status, key

    for key in ("checks", "anchors", "validators", "probes", "results"):
        value = report.get(key)
        if isinstance(value, dict):
            status = classify_mapping(value)
            if status in {"PASS", "FAIL"}:
                return status, key

    return "UNKNOWN", "cannot_derive"


def is_placeholder(value: str) -> bool:
    normalized = value.strip().upper()
    return any(token in normalized for token in PLACEHOLDER_TOKENS)


def extract_anchor_value(anchor_entry: Any) -> str:
    if isinstance(anchor_entry, str):
        candidate = anchor_entry.strip()
        return candidate if candidate and not is_placeholder(candidate) else ""

    if not isinstance(anchor_entry, dict):
        return ""

    for key in ("txid", "txId", "txID", "id", "processId", "messageId", "locator", "url"):
        value = anchor_entry.get(key)
        if isinstance(value, str):
            candidate = value.strip()
            if candidate and not is_placeholder(candidate):
                return candidate
    return ""


def canonical_assessment(canonical_config: dict[str, Any]) -> dict[str, Any]:
    model = canonical_config.get("canonicalModel")
    if not isinstance(model, str) or not model.strip():
        model = canonical_config.get("canonicalAnchorModel")
    model = (model or "").strip()

    anchors = canonical_config.get("canonicalAnchors")
    if not isinstance(anchors, dict):
        anchors = {}

    sepolia_value = extract_anchor_value(anchors.get("sepolia"))
    arweave_value = extract_anchor_value(anchors.get("arweave"))
    ao_value = extract_anchor_value(anchors.get("ao"))

    lower_keys = {str(key).lower() for key in anchors.keys()}
    bitcoin_canonical = "bitcoin" in lower_keys or "btc" in lower_keys

    canonical_ok = (
        model == "TRIPLE_PUBLIC_ANCHOR"
        and bool(sepolia_value)
        and bool(arweave_value)
        and bool(ao_value)
        and not bitcoin_canonical
    )

    return {
        "ok": canonical_ok,
        "model": model,
        "canonicalModelOk": model == "TRIPLE_PUBLIC_ANCHOR",
        "sepolia": bool(sepolia_value),
        "arweave": bool(arweave_value),
        "ao": bool(ao_value),
        "bitcoinPresentInCanonicalAnchors": bitcoin_canonical,
    }


def freeze_is_active(freeze_marker: Any) -> bool:
    if not isinstance(freeze_marker, dict):
        return False

    if freeze_marker.get("active") is True:
        return True

    for key in ("state", "status"):
        value = freeze_marker.get(key)
        if isinstance(value, str):
            normalized = value.upper()
            if "FREEZE" in normalized and "INACTIVE" not in normalized:
                return True

    return False


def as_bool(value: Any, *, default: bool) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"true", "1", "yes", "required", "enabled", "pass"}:
            return True
        if normalized in {"false", "0", "no", "optional", "disabled", "fail"}:
            return False
    return default


def load_sigstore_policy(root: Path, policy_path_arg: str) -> tuple[dict[str, Any], Path]:
    raw_path = policy_path_arg.strip() if isinstance(policy_path_arg, str) else ""
    if raw_path:
        path = Path(raw_path)
        if not path.is_absolute():
            path = root / raw_path
    else:
        path = root / "assurance/sigstore/policy.json"

    policy = read_json(path, required=False)
    if not isinstance(policy, dict):
        return {}, path
    return policy, path


def resolve_operating_mode(policy: dict[str, Any], cli_mode: str) -> str:
    if isinstance(cli_mode, str) and cli_mode.strip():
        return cli_mode.strip().upper()

    modes = policy.get("operational_modes")
    if isinstance(modes, dict):
        default_mode = modes.get("default_mode")
        if isinstance(default_mode, str) and default_mode.strip():
            return default_mode.strip().upper()
    return DEFAULT_OPERATING_MODE


def resolve_operating_mode_policy(policy: dict[str, Any], operating_mode: str) -> dict[str, Any]:
    defaults = {
        "internalCryptoRequired": True,
        "externalHybridSignatureRequired": operating_mode == "MARKET_INTEROP",
        "blockOfficialStatusOnExternalCryptoFailure": operating_mode == "MARKET_INTEROP",
    }

    modes = policy.get("operational_modes")
    if not isinstance(modes, dict):
        return defaults

    mode_entry = modes.get(operating_mode)
    if not isinstance(mode_entry, dict):
        mode_entry = modes.get(operating_mode.lower())
    if not isinstance(mode_entry, dict):
        return defaults

    return {
        "internalCryptoRequired": as_bool(
            mode_entry.get("internal_crypto_required"),
            default=defaults["internalCryptoRequired"],
        ),
        "externalHybridSignatureRequired": as_bool(
            mode_entry.get("external_hybrid_signature_required"),
            default=defaults["externalHybridSignatureRequired"],
        ),
        "blockOfficialStatusOnExternalCryptoFailure": as_bool(
            mode_entry.get("block_official_status_on_external_crypto_failure"),
            default=defaults["blockOfficialStatusOnExternalCryptoFailure"],
        ),
    }


def build_run_context(root: Path, live_report: dict[str, Any], generated_at: str) -> dict[str, str]:
    live_ctx = live_report.get("runContext") if isinstance(live_report, dict) else {}
    if not isinstance(live_ctx, dict):
        live_ctx = {}

    package_manifest = read_json(root / "PACKAGE_MANIFEST.json", required=False)
    publication_state = read_json(root / "publication/publication_state.json", required=False)

    package_id = ""
    if isinstance(package_manifest, dict):
        package_id = str(package_manifest.get("packageId") or "")

    active_target = ""
    if isinstance(publication_state, dict):
        active_target = str(publication_state.get("activeTarget") or "")

    generated_token = "".join(ch for ch in generated_at if ch.isalnum())
    run_id = (
        os.environ.get("ETHICBIT_RUN_ID")
        or str(live_ctx.get("runId") or "")
        or f"run-{generated_token}-{os.getpid()}"
    )

    release_id = (
        os.environ.get("ETHICBIT_RELEASE_ID")
        or str(live_ctx.get("releaseId") or "")
        or package_id
        or active_target
        or "UNKNOWN_RELEASE"
    )

    verification_epoch = (
        os.environ.get("ETHICBIT_VERIFICATION_EPOCH")
        or str(live_ctx.get("verificationEpoch") or "")
        or f"{generated_at[:13]}:00:00Z"
    )

    return {
        "runId": run_id,
        "releaseId": release_id,
        "verificationEpoch": verification_epoch,
    }


def resolve_crypto_mode_metadata() -> dict[str, Any]:
    metadata: dict[str, Any] = {
        "effectiveMode": os.environ.get("ETHICBIT_CRYPTO_MODE_EFFECTIVE", "unknown"),
        "mldsaMode": os.environ.get("ETHICBIT_MLDSA_MODE", "unknown"),
        "keyProvenanceMode": os.environ.get("ETHICBIT_KEY_PROVENANCE_MODE", "unknown"),
        "claimTier": os.environ.get("ETHICBIT_CRYPTO_CLAIM_TIER", "unspecified"),
    }
    audit_require_hybrid = os.environ.get("ETHICBIT_AUDIT_REQUIRE_HYBRID", "").strip()
    if audit_require_hybrid:
        metadata["auditRequireHybrid"] = audit_require_hybrid
    release_class = os.environ.get("ETHICBIT_RELEASE_CLASS", "").strip()
    if release_class:
        metadata["releaseClass"] = release_class
    return metadata


def required_algorithms_for_risk_mode(risk_mode: str, force_hybrid: bool) -> list[str]:
    normalized = risk_mode.upper().strip() or DEFAULT_RISK_MODE
    if force_hybrid:
        return ["ED25519", "ML-DSA"]
    if normalized == "STANDARD":
        return ["ED25519"]
    if normalized in {"HIGH", "GOV"}:
        return ["ED25519", "ML-DSA"]
    return ["ED25519", "ML-DSA"]


def _default_signing_command(root: Path, script_relpath: str, *, include_signature: bool) -> str:
    script_path = (root / script_relpath).resolve()
    quoted = shlex.quote(str(script_path))
    if include_signature:
        return f"{quoted} {{payload}} {{signature}}"
    return f"{quoted} {{payload}}"


def resolve_signing_command(value: str, *, root: Path, script_relpath: str, include_signature: bool) -> str:
    if isinstance(value, str) and value.strip():
        return value.strip()
    return _default_signing_command(root, script_relpath, include_signature=include_signature)


def derive_base_status(
    *,
    live_pass: bool,
    canonical_ok: bool,
    gate_pass: bool,
    freeze_active: bool,
) -> tuple[str, str]:
    if not live_pass:
        return "BLOCKED", "LIVE_FAIL"
    if not canonical_ok:
        return "BLOCKED", "CANONICAL_MISMATCH"
    if not gate_pass:
        return "DEGRADED", "HISTORICAL_GATE_FAIL"
    if freeze_active:
        return "FROZEN", "FREEZE_ACTIVE"
    return "READY", "LIVE_CANONICAL_GATE_CONVERGED"


def derive_internal_closure_status(
    *,
    canonical_ok: bool,
    gate_pass: bool,
    crypto_pass: bool,
    freeze_active: bool,
) -> str:
    if not canonical_ok:
        return "INTERNAL_CANONICAL_BLOCKED"
    if not gate_pass:
        return "INTERNAL_GATE_BLOCKED"
    if not crypto_pass:
        return "INTERNAL_CRYPTO_BLOCKED"
    if freeze_active:
        return "INTERNAL_CLOSED_FROZEN"
    return "INTERNAL_CLOSED"


def derive_external_projection_status(
    live_status: str,
    *,
    external_crypto_pass: bool,
    external_crypto_required: bool,
) -> str:
    if external_crypto_required and not external_crypto_pass:
        return "EXTERNAL_CRYPTO_INTEROP_FAIL"
    if live_status == "PASS":
        return "EXTERNAL_LIVE_CONVERGED"
    if live_status == "UNKNOWN":
        return "EXTERNAL_LIVE_UNKNOWN"
    return "EXTERNAL_LIVE_FAIL"


def main() -> int:
    parser = argparse.ArgumentParser(description="Compute official operational status from gate/live/canonical evidence")
    parser.add_argument("--root", default=".", help="Repository root")
    parser.add_argument("--strict", action="store_true", help="Exit with code 2 if status != READY")
    parser.add_argument("--require-signature", action="store_true", help="Fail if hybrid signature validation fails")
    parser.add_argument("--require-hybrid", action="store_true", help="Always require Ed25519 + ML-DSA")
    parser.add_argument("--policy-version", default=DEFAULT_POLICY_VERSION, help="Policy version to stamp in output")
    parser.add_argument("--risk-mode", default=os.environ.get("ETHICBIT_RISK_MODE", DEFAULT_RISK_MODE), help="STANDARD | HIGH | GOV")
    parser.add_argument("--ed25519-sign-cmd", default=os.environ.get("ETHICBIT_ED25519_SIGN_CMD", ""))
    parser.add_argument("--mldsa-sign-cmd", default=os.environ.get("ETHICBIT_MLDSA_SIGN_CMD", ""))
    parser.add_argument("--ed25519-verify-cmd", default=os.environ.get("ETHICBIT_ED25519_VERIFY_CMD", ""))
    parser.add_argument("--mldsa-verify-cmd", default=os.environ.get("ETHICBIT_MLDSA_VERIFY_CMD", ""))
    parser.add_argument("--ed25519-key-id", default=os.environ.get("ETHICBIT_ED25519_KEY_ID", "ED25519_UNSET"))
    parser.add_argument("--mldsa-key-id", default=os.environ.get("ETHICBIT_MLDSA_KEY_ID", "MLDSA_UNSET"))
    parser.add_argument(
        "--operating-mode",
        default=os.environ.get("ETHICBIT_OPERATIONAL_MODE", ""),
        help="SOVEREIGN_INTERNAL | MARKET_INTEROP",
    )
    parser.add_argument(
        "--sigstore-policy",
        default=os.environ.get("ETHICBIT_SIGSTORE_POLICY_PATH", "assurance/sigstore/policy.json"),
        help="Path to sigstore policy JSON (absolute or root-relative)",
    )
    args = parser.parse_args()

    build_hybrid_signature_set, verify_hybrid_signature_set, _ = _load_crypto_modules()

    risk_mode = args.risk_mode.upper().strip() or DEFAULT_RISK_MODE

    root = Path(args.root).resolve()
    ed25519_sign_cmd = resolve_signing_command(
        args.ed25519_sign_cmd,
        root=root,
        script_relpath=DEFAULT_ED25519_SIGNER,
        include_signature=False,
    )
    mldsa_sign_cmd = resolve_signing_command(
        args.mldsa_sign_cmd,
        root=root,
        script_relpath=DEFAULT_MLDSA_SIGNER,
        include_signature=False,
    )
    ed25519_verify_cmd = resolve_signing_command(
        args.ed25519_verify_cmd,
        root=root,
        script_relpath=DEFAULT_ED25519_VERIFIER,
        include_signature=True,
    )
    mldsa_verify_cmd = resolve_signing_command(
        args.mldsa_verify_cmd,
        root=root,
        script_relpath=DEFAULT_MLDSA_VERIFIER,
        include_signature=True,
    )

    sigstore_policy, sigstore_policy_path = load_sigstore_policy(root, args.sigstore_policy)
    operating_mode = resolve_operating_mode(sigstore_policy, args.operating_mode)
    operating_mode_policy = resolve_operating_mode_policy(sigstore_policy, operating_mode)

    gate_path = root / "results/GATE_REPORT.json"
    live_path = root / "artifacts/history/swarm/triple_public_anchor_live_verification.json"
    canonical_path = root / "integration/anchor_verifier/anchor_txids_real.json"
    freeze_path = root / "artifacts/runtime/publication_freeze_state.json"
    output_path = root / "artifacts/history/swarm/official_operational_status.json"

    gate_report = read_json(gate_path, required=True)
    live_report = read_json(live_path, required=True)
    canonical_config = read_json(canonical_path, required=True)
    freeze_marker = read_json(freeze_path, required=False)

    if not isinstance(gate_report, dict):
        fail(f"gate report must be a JSON object: {gate_path}")
    if not isinstance(live_report, dict):
        fail(f"live report must be a JSON object: {live_path}")
    if not isinstance(canonical_config, dict):
        fail(f"canonical config must be a JSON object: {canonical_path}")

    gate_status_raw, gate_source = derive_gate_status(gate_report)
    live_status, live_source = derive_live_status(live_report)

    canonical = canonical_assessment(canonical_config)
    canonical_ok = bool(canonical["ok"])

    freeze_active = freeze_is_active(freeze_marker)

    gate_pass = gate_status_raw == "PASS"
    live_pass = live_status == "PASS"
    divergence = gate_pass != live_pass

    if divergence and gate_pass and not live_pass:
        gate_status_effective = "DEGRADED_BY_LIVE"
    else:
        gate_status_effective = gate_status_raw

    base_status, base_reason = derive_base_status(
        live_pass=live_pass,
        canonical_ok=canonical_ok,
        gate_pass=gate_pass,
        freeze_active=freeze_active,
    )

    generated_at = now_utc_iso()
    run_context = build_run_context(root, live_report, generated_at)
    crypto_mode_metadata = resolve_crypto_mode_metadata()

    input_hashes: dict[str, str] = {
        "gateReport": sha256_file(gate_path),
        "liveReport": sha256_file(live_path),
        "canonicalConfig": sha256_file(canonical_path),
    }
    if freeze_path.exists():
        input_hashes["freezeMarker"] = sha256_file(freeze_path)

    unsigned_payload = {
        "artifactType": "official_operational_status",
        "generatedAt": generated_at,
        "policyVersion": args.policy_version,
        "runContext": run_context,
        "cryptoMode": crypto_mode_metadata,
        "officialStatus": base_status,
        "reason": base_reason,
        "reasonCodes": [base_reason],
        "divergence": divergence,
        "gateStatusRaw": gate_status_raw,
        "gateStatusRawSource": gate_source,
        "gateStatusEffective": gate_status_effective,
        "liveStatus": live_status,
        "liveStatusSource": live_source,
        "canonicalAssessment": canonical,
        "freezeActive": freeze_active,
        "integrity": {
            "inputHashes": input_hashes,
        },
        "paths": {
            "gate": str(gate_path),
            "live": str(live_path),
            "canonical": str(canonical_path),
            "freeze": str(freeze_path),
            "output": str(output_path),
        },
    }

    unsigned_bytes = canonical_json_bytes(unsigned_payload)
    output_hash = sha256_bytes(unsigned_bytes)
    unsigned_payload["integrity"]["outputHash"] = output_hash

    required_algorithms = required_algorithms_for_risk_mode(risk_mode, args.require_hybrid)
    signature_set, _ = build_hybrid_signature_set(
        unsigned_payload,
        policy_version=args.policy_version,
        run_context=run_context,
        risk_mode=risk_mode,
        ed25519_sign_cmd=ed25519_sign_cmd,
        mldsa_sign_cmd=mldsa_sign_cmd,
        ed25519_key_id=args.ed25519_key_id,
        mldsa_key_id=args.mldsa_key_id,
        required_algorithms=required_algorithms,
        crypto_mode=crypto_mode_metadata,
    )

    signature_verification = verify_hybrid_signature_set(
        unsigned_payload,
        signature_set,
        risk_mode=risk_mode,
        ed25519_verify_cmd=ed25519_verify_cmd,
        mldsa_verify_cmd=mldsa_verify_cmd,
        required_algorithms=required_algorithms,
    )

    external_crypto_pass = signature_set.get("status") == "PASS" and signature_verification.get("status") == "PASS"
    internal_crypto_pass = bool(unsigned_payload["integrity"].get("outputHash"))
    if not operating_mode_policy["internalCryptoRequired"]:
        internal_crypto_pass = True

    effective_external_required = operating_mode_policy["externalHybridSignatureRequired"] or args.require_signature
    crypto_pass = internal_crypto_pass and (external_crypto_pass or not effective_external_required)

    final_status = base_status
    final_reason = base_reason
    reason_codes = [base_reason]

    if not internal_crypto_pass:
        reason_codes.append("INTERNAL_CRYPTO_FAIL")
        if base_reason != "LIVE_FAIL":
            final_status = "BLOCKED"
            final_reason = "CRYPTO_POLICY_FAIL"
    if not external_crypto_pass:
        reason_codes.append("EXTERNAL_CRYPTO_INTEROP_FAIL")
    if effective_external_required and not external_crypto_pass:
        reason_codes.append("CRYPTO_POLICY_FAIL")
        if operating_mode_policy["blockOfficialStatusOnExternalCryptoFailure"] and base_reason != "LIVE_FAIL":
            final_status = "BLOCKED"
            final_reason = "CRYPTO_POLICY_FAIL"

    require_signature_failed = args.require_signature and not external_crypto_pass

    internal_closure_status = derive_internal_closure_status(
        canonical_ok=canonical_ok,
        gate_pass=gate_pass,
        crypto_pass=internal_crypto_pass,
        freeze_active=freeze_active,
    )
    external_projection_status = derive_external_projection_status(
        live_status,
        external_crypto_pass=external_crypto_pass,
        external_crypto_required=operating_mode_policy["externalHybridSignatureRequired"],
    )

    unsigned_payload["officialStatus"] = final_status
    unsigned_payload["officialOperationalStatus"] = final_status
    unsigned_payload["reason"] = final_reason
    unsigned_payload["reasonCodes"] = sorted(set(reason_codes), key=reason_codes.index)
    unsigned_payload["internalClosureStatus"] = internal_closure_status
    unsigned_payload["externalProjectionStatus"] = external_projection_status
    unsigned_payload["internalCryptographyStatus"] = "PASS" if internal_crypto_pass else "FAIL"
    unsigned_payload["externalCryptographyStatus"] = "PASS" if external_crypto_pass else "FAIL"
    unsigned_payload["stateModel"] = {
        "model": "SOVEREIGN_INTERNAL_CLOSURE_PLUS_EXTERNAL_PROJECTION_V1",
        "operatingMode": operating_mode,
        "internalClosureStatus": internal_closure_status,
        "externalProjectionStatus": external_projection_status,
        "officialOperationalStatus": final_status,
    }
    unsigned_payload["cryptography"] = {
        "status": "PASS" if crypto_pass else "FAIL",
        "operatingMode": operating_mode,
        "riskMode": risk_mode,
        "executionMode": crypto_mode_metadata,
        "requiredAlgorithms": required_algorithms,
        "internal": {
            "status": "PASS" if internal_crypto_pass else "FAIL",
            "required": bool(operating_mode_policy["internalCryptoRequired"]),
            "mechanism": "CANONICAL_PAYLOAD_HASH_BINDING",
        },
        "external": {
            "status": "PASS" if external_crypto_pass else "FAIL",
            "required": bool(operating_mode_policy["externalHybridSignatureRequired"]),
            "blocking": bool(operating_mode_policy["blockOfficialStatusOnExternalCryptoFailure"]),
            "algorithm": "HYBRID_ED25519_MLDSA",
        },
        "policyPath": str(sigstore_policy_path),
    }
    unsigned_payload["policyBinding"] = {
        "sigstorePolicyPath": str(sigstore_policy_path),
        "operatingMode": operating_mode,
        "internalCryptoRequired": bool(operating_mode_policy["internalCryptoRequired"]),
        "externalHybridSignatureRequired": bool(operating_mode_policy["externalHybridSignatureRequired"]),
        "blockOfficialStatusOnExternalCryptoFailure": bool(
            operating_mode_policy["blockOfficialStatusOnExternalCryptoFailure"]
        ),
    }

    output = dict(unsigned_payload)
    output["signature"] = {
        "status": "SIGNED_HYBRID" if external_crypto_pass else "INVALID_OR_MISSING",
        "algorithm": "HYBRID_ED25519_MLDSA",
        "keyIds": [args.ed25519_key_id, args.mldsa_key_id],
    }
    output["signatureSet"] = signature_set
    output["signatureVerification"] = signature_verification

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as handle:
        json.dump(output, handle, indent=2, ensure_ascii=False)
        handle.write("\n")

    if require_signature_failed:
        fail("hybrid signatures are required but validation failed")

    print(final_status)
    print(
        "DETAIL: "
        f"reason={final_reason}; live={live_status}; gate_raw={gate_status_raw}; "
        f"gate_effective={gate_status_effective}; canonical_ok={canonical_ok}; "
        f"freeze_active={freeze_active}; divergence={divergence}; "
        f"crypto_internal={'PASS' if internal_crypto_pass else 'FAIL'}; "
        f"crypto_external={'PASS' if external_crypto_pass else 'FAIL'}; "
        f"crypto_effective={'PASS' if crypto_pass else 'FAIL'}; "
        f"mode={operating_mode}; "
        f"internal={internal_closure_status}; external={external_projection_status}; "
        f"output={output_path}"
    )

    if args.strict and final_status != "READY":
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
