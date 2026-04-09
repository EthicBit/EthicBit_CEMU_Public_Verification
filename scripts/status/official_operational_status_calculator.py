#!/usr/bin/env python3
"""
Official Operational Status Calculator
EthicBit / CEMU v3.7.0+
"""

import argparse
import hashlib
import hmac
import json
import os
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
    "READY_FOR_CONTROLLED_PRODUCTION_CANDIDATE",
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
DEFAULT_POLICY_VERSION = "official-operational-status-policy.v1.0.0"


def fail(message: str) -> None:
    raise SystemExit(f"OFFICIAL_STATUS_INVALID: {message}")


def now_utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def canonical_json_bytes(payload: dict[str, Any]) -> bytes:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


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


def load_signing_key() -> tuple[str, str]:
    key = os.environ.get("OFFICIAL_STATUS_SIGNING_KEY", "")
    key_file = os.environ.get("OFFICIAL_STATUS_SIGNING_KEY_FILE", "")
    key_id = os.environ.get("OFFICIAL_STATUS_SIGNING_KEY_ID", "UNSET")

    if not key and key_file:
        path = Path(key_file)
        if not path.exists():
            fail(f"signing key file not found: {path}")
        key = path.read_text(encoding="utf-8").strip()

    return key, key_id


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


def main() -> int:
    parser = argparse.ArgumentParser(description="Compute official operational status from gate/live/canonical evidence")
    parser.add_argument("--root", default=".", help="Repository root")
    parser.add_argument("--strict", action="store_true", help="Exit with code 2 if status != READY")
    parser.add_argument("--require-signature", action="store_true", help="Fail if signing key is not configured")
    parser.add_argument("--policy-version", default=DEFAULT_POLICY_VERSION, help="Policy version to stamp in output")
    args = parser.parse_args()

    root = Path(args.root).resolve()

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

    if not live_pass:
        official_status = "BLOCKED"
        reason = "LIVE_FAIL"
    elif not canonical_ok:
        official_status = "BLOCKED"
        reason = "CANONICAL_MISMATCH"
    elif not gate_pass:
        official_status = "DEGRADED"
        reason = "HISTORICAL_GATE_FAIL"
    elif freeze_active:
        official_status = "FROZEN"
        reason = "FREEZE_ACTIVE"
    else:
        official_status = "READY"
        reason = "LIVE_CANONICAL_GATE_CONVERGED"

    generated_at = now_utc_iso()
    run_context = build_run_context(root, live_report, generated_at)

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
        "officialStatus": official_status,
        "reason": reason,
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

    signing_key, signing_key_id = load_signing_key()
    signature_value = ""
    signature_status = "UNSIGNED"

    if signing_key:
        signature_value = hmac.new(signing_key.encode("utf-8"), unsigned_bytes, hashlib.sha256).hexdigest()
        signature_status = "SIGNED"
    elif args.require_signature:
        fail("signature required but OFFICIAL_STATUS_SIGNING_KEY/FILE is not configured")

    output = dict(unsigned_payload)
    output["signature"] = {
        "status": signature_status,
        "algorithm": "HMAC-SHA256",
        "keyId": signing_key_id,
        "value": signature_value,
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as handle:
        json.dump(output, handle, indent=2, ensure_ascii=False)
        handle.write("\n")

    print(official_status)
    print(
        "DETAIL: "
        f"reason={reason}; live={live_status}; gate_raw={gate_status_raw}; "
        f"gate_effective={gate_status_effective}; canonical_ok={canonical_ok}; "
        f"freeze_active={freeze_active}; divergence={divergence}; signature={signature_status}; output={output_path}"
    )

    if args.strict and official_status != "READY":
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
