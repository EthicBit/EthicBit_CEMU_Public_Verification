#!/usr/bin/env python3
"""
Anchor AEM-EVOLVE Technical Demonstration manifest on Ethereum mainnet.

Safety controls:
  - DRY_RUN=1 prints payload and validates network, never broadcasts.
  - BROADCAST=1 is required for a real broadcast.
  - Canonical manifest SHA-256 must match the official hash record.

Env vars:
  DRY_RUN=1
  BROADCAST=1
  ETHICBIT_MAINNET_RPC_URL=https://...
  ETH_RPC_URL=https://...                         # fallback alias
  ETHICBIT_PRIVATE_KEY=0x...
  ETH_PRIVATE_KEY=0x...                           # fallback alias
  ETHICBIT_AEM_EVOLVE_EXPECTED_SHA256=<hex64>     # optional override
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import sys
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]

MANIFEST_PATH = ROOT / "assurance" / "evolve" / "AEM_EVOLVE_MANIFEST.json"
HASH_RECORD_PATH = ROOT / "assurance" / "evolve" / "AEM_EVOLVE_HASH_RECORD.txt"
TECHNICAL_RECEIPT_PATH = (
    ROOT / "receipts" / "AEM_EVOLVE_TECHNICAL_DEMONSTRATION_RECEIPT.json"
)
REGISTRY_RECEIPT_PATH = (
    ROOT
    / "receipts"
    / "ETHICBIT_CEMU_AEM_V1_1_GLOBAL_PUBLIC_VERIFICATION_REGISTRY_MAINNET_ANCHOR_RECEIPT.json"
)
SUPPLY_CHAIN_ANCHOR_RECEIPT_PATH = (
    ROOT / "receipts" / "AEM_V1_1_SUPPLY_CHAIN_VERIFICATION_EXTENSION_MAINNET_ANCHOR_RECEIPT.json"
)
REPRODUCIBILITY_ANCHOR_RECEIPT_PATH = (
    ROOT / "receipts" / "AEM_V1_1_REPRODUCIBILITY_EXTENSION_MAINNET_ANCHOR_RECEIPT.json"
)
RELEASE_ZIP_PATH = (
    ROOT / "artifacts" / "releases" / "AEM_EVOLVE_TECHNICAL_DEMONSTRATION_v0_3.zip"
)
RELEASE_SHA_PATH = (
    ROOT / "artifacts" / "releases" / "AEM_EVOLVE_TECHNICAL_DEMONSTRATION_v0_3.sha256"
)
ANCHOR_RECEIPT_PATH = (
    ROOT / "receipts" / "AEM_EVOLVE_TECHNICAL_DEMONSTRATION_MAINNET_ANCHOR_RECEIPT.json"
)

DEFAULT_EXPECTED_CANONICAL_SHA = (
    "7e5f3f735a01e317514cb5e93559be5ed42496ea89058f98e1fc15eb5407d7cf"
)

SCHEMA_ID = "ETHICBIT_AEM_EVOLVE_TECHNICAL_DEMONSTRATION_MAINNET_ANCHOR_PAYLOAD_V1"
RECEIPT_SCHEMA_ID = (
    "ETHICBIT_AEM_EVOLVE_TECHNICAL_DEMONSTRATION_MAINNET_ANCHOR_RECEIPT_V1"
)

RELEASE_TAG = "aem-evolve-technical-demonstration-v0.3-2026-05"
RELEASE_TARGET_COMMIT = "05de8055deb547248c4c35585090401b33c98e62"
RELEASE_URL = (
    "https://github.com/EthicBit/EthicBit_CEMU/releases/tag/"
    "aem-evolve-technical-demonstration-v0.3-2026-05"
)

NETWORK = "ethereum-mainnet"
CHAIN_ID = 1


def _now_utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _sha256_file(path: Path) -> str:
    return _sha256_bytes(path.read_bytes())


def _sha256_canonical_json(path: Path) -> str:
    obj = json.loads(path.read_text(encoding="utf-8"))
    payload = json.dumps(
        obj,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return _sha256_bytes(payload)


def _rpc_endpoints() -> list[str]:
    preferred = os.environ.get("ETHICBIT_MAINNET_RPC_URL", "").strip() or os.environ.get(
        "ETH_RPC_URL", ""
    ).strip()
    base = [
        "https://ethereum-rpc.publicnode.com",
        "https://eth.llamarpc.com",
        "https://1rpc.io/eth",
        "https://rpc.ankr.com/eth",
    ]
    if preferred:
        return [preferred] + [x for x in base if x != preferred]
    return base


def _rpc_call(rpcs: list[str], method: str, params: list, timeout: int = 25):
    body = json.dumps(
        {"jsonrpc": "2.0", "id": 1, "method": method, "params": params}
    ).encode()
    last_error = None
    for rpc in rpcs:
        try:
            req = urllib.request.Request(
                rpc,
                data=body,
                headers={"Content-Type": "application/json", "User-Agent": "curl/8.0"},
            )
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                payload = json.loads(resp.read())
            if "result" in payload:
                return payload["result"], rpc
            last_error = f"{rpc}: {payload.get('error')}"
        except Exception as exc:  # noqa: BLE001
            last_error = f"{rpc}: {str(exc)[:160]}"
    raise RuntimeError(f"all RPCs failed for {method}: {last_error}")


def _read_private_key() -> str:
    value = os.environ.get("ETHICBIT_PRIVATE_KEY", "").strip() or os.environ.get(
        "ETH_PRIVATE_KEY", ""
    ).strip()
    if not value:
        raise RuntimeError("missing ETHICBIT_PRIVATE_KEY (or ETH_PRIVATE_KEY)")
    if value.startswith("0x"):
        key = value[2:]
    else:
        key = value
    if not re.fullmatch(r"[0-9a-fA-F]{64}", key):
        raise RuntimeError(f"private_key must contain exactly 64 hex digits (got {len(key)})")
    return "0x" + key


def _expected_canonical_hash() -> str:
    env_override = os.environ.get("ETHICBIT_AEM_EVOLVE_EXPECTED_SHA256", "").strip().lower()
    if env_override:
        return env_override

    if HASH_RECORD_PATH.exists():
        text = HASH_RECORD_PATH.read_text(encoding="utf-8")
        m = re.search(r"Manifest canonical SHA-256:\s*([0-9a-fA-F]{64})", text)
        if m:
            return m.group(1).lower()

    return DEFAULT_EXPECTED_CANONICAL_SHA


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _release_zip_sha256() -> str:
    if RELEASE_SHA_PATH.exists():
        text = RELEASE_SHA_PATH.read_text(encoding="utf-8").strip()
        first = text.split()[0].lower()
        if re.fullmatch(r"[0-9a-f]{64}", first):
            return first
    return _sha256_file(RELEASE_ZIP_PATH)


def _build_payload(
    manifest_canonical_sha: str,
    manifest_file_sha: str,
    release_zip_sha: str,
    technical_receipt: dict,
    registry_receipt: dict,
    supply_chain_receipt: dict,
    reproducibility_receipt: dict,
) -> dict:
    return {
        "schema_id": SCHEMA_ID,
        "extension_name": "AEM-EVOLVE",
        "release_name": "AEM-EVOLVE Technical Demonstration Release v0.3",
        "release_tag": RELEASE_TAG,
        "release_target_commit": RELEASE_TARGET_COMMIT,
        "release_url": RELEASE_URL,
        "current_status": "CONCEPT_CONTROLLED_TECHNICAL_DEMONSTRATION",
        "manifest_canonical_sha256": manifest_canonical_sha,
        "manifest_file_sha256": manifest_file_sha,
        "manifest_canonicalization": "json_sort_keys_no_whitespace_utf8",
        "manifest_hash_algorithm": "SHA-256",
        "manifest_relative_path": str(MANIFEST_PATH.relative_to(ROOT)),
        "hash_record_relative_path": str(HASH_RECORD_PATH.relative_to(ROOT)),
        "release_zip_relative_path": str(RELEASE_ZIP_PATH.relative_to(ROOT)),
        "release_zip_sha256": release_zip_sha,
        "technical_receipt_schema_id": technical_receipt.get("schema_id"),
        "technical_receipt_status": technical_receipt.get("status"),
        "demo_status": technical_receipt.get("demo_status"),
        "event_id": technical_receipt.get("event_id"),
        "evolution_receipt_id": technical_receipt.get("evolution_receipt_id"),
        "outcome": technical_receipt.get("outcome"),
        "claim_scope": technical_receipt.get("claim_scope"),
        "signature_verified": bool(technical_receipt.get("signature_verified")),
        "registry_anchor_tx_hash": registry_receipt.get("tx_hash"),
        "registry_anchor_block_number": registry_receipt.get("block_number"),
        "registry_anchor_status": registry_receipt.get("status"),
        "supply_chain_extension_anchor_tx_hash": supply_chain_receipt.get("tx_hash"),
        "supply_chain_extension_anchor_block_number": supply_chain_receipt.get("block_number"),
        "supply_chain_extension_anchor_status": supply_chain_receipt.get("status"),
        "reproducibility_extension_anchor_tx_hash": reproducibility_receipt.get("tx_hash"),
        "reproducibility_extension_anchor_block_number": reproducibility_receipt.get(
            "block_number"
        ),
        "reproducibility_extension_anchor_status": reproducibility_receipt.get("status"),
        "production_ready_claimed": False,
        "lab_ready_claimed": False,
        "clinical_validation_claimed": False,
        "clinical_claimed": False,
        "diagnostic_claimed": False,
        "regulatory_approval_claimed": False,
        "gxp_certification_claimed": False,
        "fda_ema_acceptance_claimed": False,
        "independently_reproduced": False,
        "third_party_binding": False,
        "patent_grant_claimed": False,
        "uspto_approval_claimed": False,
        "court_recognition_claimed": False,
        "ts_unix": int(time.time()),
    }


def main() -> int:
    dry_run = os.environ.get("DRY_RUN") == "1"
    broadcast = os.environ.get("BROADCAST") == "1"
    rpcs = _rpc_endpoints()

    required_paths = [
        MANIFEST_PATH,
        HASH_RECORD_PATH,
        TECHNICAL_RECEIPT_PATH,
        REGISTRY_RECEIPT_PATH,
        SUPPLY_CHAIN_ANCHOR_RECEIPT_PATH,
        REPRODUCIBILITY_ANCHOR_RECEIPT_PATH,
        RELEASE_ZIP_PATH,
        RELEASE_SHA_PATH,
    ]
    missing = [str(p) for p in required_paths if not p.exists()]
    if missing:
        print("ERROR: missing required AEM-EVOLVE anchor inputs:", file=sys.stderr)
        for item in missing:
            print(f" - {item}", file=sys.stderr)
        return 1

    manifest_canonical_sha = _sha256_canonical_json(MANIFEST_PATH)
    manifest_file_sha = _sha256_file(MANIFEST_PATH)
    release_zip_sha = _release_zip_sha256()
    expected_sha = _expected_canonical_hash()

    print("=== AEM-EVOLVE MANIFEST HASH CHECK ===")
    print(f"manifest_path       = {MANIFEST_PATH}")
    print(f"canonical_sha256    = {manifest_canonical_sha}")
    print(f"file_sha256         = {manifest_file_sha}")
    print(f"expected_canonical  = {expected_sha}")
    print(f"release_zip_sha256  = {release_zip_sha}")
    print("NOTE: canonical and file SHA-256 may differ by design.")

    if manifest_canonical_sha.lower() != expected_sha.lower():
        print(
            "ERROR: AEM-EVOLVE manifest canonical hash does not match expected hash record.",
            file=sys.stderr,
        )
        return 1

    technical_receipt = _read_json(TECHNICAL_RECEIPT_PATH)
    registry_receipt = _read_json(REGISTRY_RECEIPT_PATH)
    supply_chain_receipt = _read_json(SUPPLY_CHAIN_ANCHOR_RECEIPT_PATH)
    reproducibility_receipt = _read_json(REPRODUCIBILITY_ANCHOR_RECEIPT_PATH)

    payload = _build_payload(
        manifest_canonical_sha=manifest_canonical_sha,
        manifest_file_sha=manifest_file_sha,
        release_zip_sha=release_zip_sha,
        technical_receipt=technical_receipt,
        registry_receipt=registry_receipt,
        supply_chain_receipt=supply_chain_receipt,
        reproducibility_receipt=reproducibility_receipt,
    )
    payload_bytes = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    payload_sha = _sha256_bytes(payload_bytes)

    print("\n=== AEM-EVOLVE ANCHOR PAYLOAD ===")
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    print(f"payload_sha256 = {payload_sha}")
    print(f"payload_bytes  = {len(payload_bytes)}")

    chain_hex, chain_rpc = _rpc_call(rpcs, "eth_chainId", [])
    chain_id = int(chain_hex, 16)
    print("\n=== NETWORK CHECK ===")
    print(f"rpc_endpoint   = {chain_rpc}")
    print(f"network        = {NETWORK}")
    print(f"chain_id       = {chain_id}")
    if chain_id != CHAIN_ID:
        print(f"ERROR: wrong chain id (expected {CHAIN_ID}, got {chain_id})", file=sys.stderr)
        return 1

    if dry_run:
        existing_status = "NONE"
        existing_tx = "N/A"
        if ANCHOR_RECEIPT_PATH.exists():
            try:
                existing = _read_json(ANCHOR_RECEIPT_PATH)
                existing_status = existing.get("status", "UNKNOWN")
                existing_tx = existing.get("tx_hash", "N/A")
            except Exception:  # noqa: BLE001
                pass
        print("\nDRY_RUN=1: no transaction will be broadcast.")
        print(
            "NOTE: current run is dry-run only; existing AEM-EVOLVE anchor "
            f"status={existing_status} tx={existing_tx}"
        )
        return 0

    if not broadcast:
        print(
            "ERROR: refusing to broadcast without BROADCAST=1 (run DRY_RUN=1 first).",
            file=sys.stderr,
        )
        return 1

    try:
        from eth_account import Account

        private_key = _read_private_key()
    except Exception as exc:  # noqa: BLE001
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    acct = Account.from_key(private_key)
    sender = acct.address

    nonce_hex, nonce_rpc = _rpc_call(rpcs, "eth_getTransactionCount", [sender, "latest"])
    nonce = int(nonce_hex, 16)

    try:
        fee_hist, fee_rpc = _rpc_call(rpcs, "eth_feeHistory", [hex(4), "latest", [50]])
        base_fee = int(fee_hist["baseFeePerGas"][-1], 16)
    except Exception:  # noqa: BLE001
        fee_rpc = chain_rpc
        base_fee = int((_rpc_call(rpcs, "eth_gasPrice", [])[0]), 16)

    max_priority = 2 * 10**9
    max_fee = base_fee * 2 + max_priority

    estimate_tx = {
        "from": sender,
        "to": sender,
        "value": "0x0",
        "data": "0x" + payload_bytes.hex(),
        "type": "0x2",
    }
    gas_hex, gas_rpc = _rpc_call(rpcs, "eth_estimateGas", [estimate_tx])
    gas_limit = int(gas_hex, 16) + 5000

    tx = {
        "type": 2,
        "chainId": CHAIN_ID,
        "nonce": nonce,
        "to": sender,
        "value": 0,
        "data": payload_bytes,
        "gas": gas_limit,
        "maxPriorityFeePerGas": max_priority,
        "maxFeePerGas": max_fee,
    }

    print("\n=== BROADCAST PLAN ===")
    print(f"from/to        = {sender}")
    print(f"nonce          = {nonce} (via {nonce_rpc})")
    print(f"gas_limit      = {gas_limit} (via {gas_rpc})")
    print(f"max_fee_gwei   = {max_fee / 1e9:.3f} (fee source: {fee_rpc})")
    print(f"max_pri_gwei   = {max_priority / 1e9:.3f}")
    print(f"max_fee_wei    = {gas_limit * max_fee}")

    signed = Account.sign_transaction(tx, private_key=private_key)
    raw_tx = getattr(signed, "raw_transaction", None) or signed.rawTransaction
    tx_hash_hex, send_rpc = _rpc_call(rpcs, "eth_sendRawTransaction", ["0x" + raw_tx.hex()])
    print("\n=== TX SENT ===")
    print(f"tx_hash        = {tx_hash_hex}")
    print(f"broadcast_rpc  = {send_rpc}")
    print("waiting for receipt...")

    receipt = None
    receipt_rpc = None
    for _ in range(72):
        try:
            rr, rr_rpc = _rpc_call(rpcs, "eth_getTransactionReceipt", [tx_hash_hex])
            if rr:
                receipt = rr
                receipt_rpc = rr_rpc
                break
        except Exception:  # noqa: BLE001
            pass
        time.sleep(5)

    if receipt is None:
        print("ERROR: transaction receipt not found in expected window", file=sys.stderr)
        return 1

    status = int(receipt.get("status", "0x0"), 16)
    block_number = int(receipt.get("blockNumber", "0x0"), 16)
    gas_used = int(receipt.get("gasUsed", "0x0"), 16)
    eff_gas = int(receipt.get("effectiveGasPrice", hex(max_fee)), 16)
    fee_paid_wei = gas_used * eff_gas

    tx_data, tx_lookup_rpc = _rpc_call(rpcs, "eth_getTransactionByHash", [tx_hash_hex])
    if tx_data is None:
        tx_data = {}

    anchor_receipt = {
        "schema_id": RECEIPT_SCHEMA_ID,
        "status": (
            "ONCHAIN_AEM_EVOLVE_TECHNICAL_DEMONSTRATION_ANCHOR_VERIFIED"
            if status == 1
            else "ONCHAIN_AEM_EVOLVE_TECHNICAL_DEMONSTRATION_ANCHOR_FAILED"
        ),
        "network": NETWORK,
        "chain_id": CHAIN_ID,
        "tx_hash": tx_hash_hex,
        "block_number": block_number,
        "block_explorer_url": f"https://etherscan.io/tx/{tx_hash_hex}",
        "timestamp_utc": _now_utc_iso(),
        "from_address": tx_data.get("from", sender).lower(),
        "to_address": tx_data.get("to", sender).lower(),
        "gas_used": gas_used,
        "effective_gas_price_wei": eff_gas,
        "fee_paid_wei": fee_paid_wei,
        "fee_paid_eth": fee_paid_wei / 10**18,
        "payload": payload,
        "payload_sha256": payload_sha,
        "extension_manifest": {
            "manifest_path": str(MANIFEST_PATH.relative_to(ROOT)),
            "manifest_canonical_sha256": manifest_canonical_sha,
            "manifest_file_sha256": manifest_file_sha,
            "hash_algorithm": "SHA-256",
            "canonicalization": "json_sort_keys_no_whitespace_utf8",
        },
        "release_artifact": {
            "release_tag": RELEASE_TAG,
            "release_target_commit": RELEASE_TARGET_COMMIT,
            "release_url": RELEASE_URL,
            "zip_path": str(RELEASE_ZIP_PATH.relative_to(ROOT)),
            "zip_sha256": release_zip_sha,
        },
        "verification_rpcs": {
            "broadcast": send_rpc,
            "receipt_lookup": receipt_rpc,
            "tx_lookup": tx_lookup_rpc,
            "chain_check": chain_rpc,
            "nonce_lookup": nonce_rpc,
            "gas_estimate": gas_rpc,
        },
    }

    ANCHOR_RECEIPT_PATH.parent.mkdir(parents=True, exist_ok=True)
    ANCHOR_RECEIPT_PATH.write_text(
        json.dumps(anchor_receipt, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    print("\n=== RECEIPT WRITTEN ===")
    print(ANCHOR_RECEIPT_PATH)
    print(f"status         = {anchor_receipt['status']}")
    print(f"block_number   = {block_number}")
    print(f"fee_paid_eth   = {anchor_receipt['fee_paid_eth']:.10f}")
    print(f"receipt_rpc    = {receipt_rpc}")

    return 0 if status == 1 else 1


if __name__ == "__main__":
    raise SystemExit(main())
