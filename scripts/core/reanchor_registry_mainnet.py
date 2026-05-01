#!/usr/bin/env python3
"""
Anchor AEM V1.1 Global Public Verification Registry on Ethereum mainnet.

Safety controls:
  - DRY_RUN=1 prints payload and tx plan, never broadcasts.
  - BROADCAST=1 is required for a real broadcast.
  - Canonical registry SHA-256 must match the official expected hash.

Env vars:
  DRY_RUN=1
  BROADCAST=1
  ETHICBIT_MAINNET_RPC_URL=https://...
  ETH_RPC_URL=https://...                    # fallback alias
  ETHICBIT_PRIVATE_KEY=0x...
  ETH_PRIVATE_KEY=0x...                      # fallback alias
  ETHICBIT_REGISTRY_EXPECTED_SHA256=<hex64> # optional override
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

from eth_account import Account


ROOT = Path(__file__).resolve().parents[2]
REGISTRY_PATH = (
    ROOT / "registry" / "ETHICBIT_CEMU_AEM_V1_1_GLOBAL_PUBLIC_VERIFICATION_REGISTRY.json"
)
HASH_RECORD_PATH = (
    ROOT
    / "registry"
    / "ETHICBIT_CEMU_AEM_V1_1_GLOBAL_PUBLIC_VERIFICATION_REGISTRY_HASH_RECORD.txt"
)
RECEIPT_PATH = (
    ROOT
    / "receipts"
    / "ETHICBIT_CEMU_AEM_V1_1_GLOBAL_PUBLIC_VERIFICATION_REGISTRY_MAINNET_ANCHOR_RECEIPT.json"
)

DEFAULT_EXPECTED_CANONICAL_SHA = (
    "24b813071b7dac3ae29ac4571945f846554244ccea52e2b61c3ad4b6894ca075"
)

SCHEMA_ID = (
    "ETHICBIT_CEMU_AEM_V1_1_GLOBAL_PUBLIC_VERIFICATION_REGISTRY_MAINNET_ANCHOR_PAYLOAD_V1"
)
RECEIPT_SCHEMA_ID = (
    "ETHICBIT_CEMU_AEM_V1_1_GLOBAL_PUBLIC_VERIFICATION_REGISTRY_MAINNET_ANCHOR_RECEIPT_V1"
)

NETWORK = "ethereum-mainnet"
CHAIN_ID = 1

AEM_V1_1_ANCHOR_TX = "0xa0a354162c5d2e2eb3a45ecd6bb34f0a57ac093d2674e5fb5eed87e4551165c0"
AEM_V1_1_FREEZE_PDF_SHA256 = (
    "689992b6e73ffd897dfc75112abeda022cee6ad492037217f7bab28397b69696"
)
AEM_V1_1_PUBLIC_KIT_ZIP_SHA256 = (
    "a3933a6cac4badb07c29b0ed17f8529a059730e9a7d5efde0884afdcd96c98a0"
)


def _now_utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _canonical_json_bytes(obj: dict) -> bytes:
    return json.dumps(
        obj,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")


def _registry_hashes(path: Path) -> tuple[str, str]:
    obj = json.loads(path.read_text(encoding="utf-8"))
    canonical_hash = hashlib.sha256(_canonical_json_bytes(obj)).hexdigest()
    file_hash = hashlib.sha256(path.read_bytes()).hexdigest()
    return canonical_hash, file_hash


def _expected_canonical_hash() -> str:
    env_override = os.environ.get("ETHICBIT_REGISTRY_EXPECTED_SHA256", "").strip().lower()
    if env_override:
        return env_override

    if HASH_RECORD_PATH.exists():
        text = HASH_RECORD_PATH.read_text(encoding="utf-8")
        m = re.search(
            r"SHA-256 \(canonicalized JSON:[^)]+\):\s*([0-9a-fA-F]{64})",
            text,
            flags=re.S,
        )
        if m:
            return m.group(1).lower()

    return DEFAULT_EXPECTED_CANONICAL_SHA


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
    if not value.startswith("0x"):
        value = "0x" + value
    return value


def _build_payload(registry_sha256: str) -> dict:
    return {
        "schema_id": SCHEMA_ID,
        "technology_artifact": "AEM V1.1 - Mechanical Ethical Agent",
        "technology_version": "AEM V1.1",
        "registry_name": "AEM V1.1 - Global Public Verification Registry",
        "registry_schema_version": "V1.0",
        "registry_sha256": registry_sha256,
        "registry_canonicalization": "json_sort_keys_no_whitespace_utf8",
        "registry_hash_algorithm": "SHA-256",
        "aem_v1_1_anchor_tx": AEM_V1_1_ANCHOR_TX,
        "aem_v1_1_freeze_pdf_sha256": AEM_V1_1_FREEZE_PDF_SHA256,
        "aem_v1_1_public_kit_zip_sha256": AEM_V1_1_PUBLIC_KIT_ZIP_SHA256,
        "historical_claim_level_ceiling": "L5",
        "historical_constitutional_controls": "14/14 PASS",
        "historical_tampering_resistance": "PROVEN",
        "third_party_binding": False,
        "presentation_scope": "READY_WITH_SCOPE_DELIMITATION",
        "filing_reference_scope": "administrative_reference_only",
        "patent_grant_claimed": False,
        "uspto_approval_claimed": False,
        "regulatory_approval_claimed": False,
        "court_recognition_claimed": False,
        "ts_unix": int(time.time()),
    }


def main() -> int:
    dry_run = os.environ.get("DRY_RUN") == "1"
    broadcast = os.environ.get("BROADCAST") == "1"
    rpcs = _rpc_endpoints()

    if not REGISTRY_PATH.exists():
        print(f"ERROR: missing registry file: {REGISTRY_PATH}", file=sys.stderr)
        return 1

    canonical_sha, file_sha = _registry_hashes(REGISTRY_PATH)
    expected_sha = _expected_canonical_hash()

    print("=== REGISTRY HASH CHECK ===")
    print(f"registry_path      = {REGISTRY_PATH}")
    print(f"canonical_sha256   = {canonical_sha}")
    print(f"file_sha256        = {file_sha}")
    print(f"expected_canonical = {expected_sha}")
    if canonical_sha.lower() != expected_sha.lower():
        print(
            "ERROR: canonical registry hash does not match expected official hash.",
            file=sys.stderr,
        )
        return 1

    payload = _build_payload(canonical_sha)
    payload_bytes = _canonical_json_bytes(payload)
    payload_sha = hashlib.sha256(payload_bytes).hexdigest()

    print("\n=== REGISTRY ANCHOR PAYLOAD ===")
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
        print("\nDRY_RUN=1: no transaction will be broadcast.")
        return 0

    if not broadcast:
        print(
            "ERROR: refusing to broadcast without BROADCAST=1 (run DRY_RUN=1 first).",
            file=sys.stderr,
        )
        return 1

    try:
        private_key = _read_private_key()
    except RuntimeError as exc:
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
    for _ in range(72):  # ~6 min at 5s interval
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
            "ONCHAIN_REGISTRY_ANCHOR_VERIFIED"
            if status == 1
            else "ONCHAIN_REGISTRY_ANCHOR_FAILED"
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
        "registry": {
            "registry_path": str(REGISTRY_PATH.relative_to(ROOT)),
            "registry_canonical_sha256": canonical_sha,
            "registry_file_sha256": file_sha,
            "registry_canonicalization": "json_sort_keys_no_whitespace_utf8",
            "hash_algorithm": "SHA-256",
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

    RECEIPT_PATH.parent.mkdir(parents=True, exist_ok=True)
    RECEIPT_PATH.write_text(
        json.dumps(anchor_receipt, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    print("\n=== RECEIPT WRITTEN ===")
    print(RECEIPT_PATH)
    print(f"status         = {anchor_receipt['status']}")
    print(f"block_number   = {block_number}")
    print(f"fee_paid_eth   = {anchor_receipt['fee_paid_eth']:.10f}")
    print(f"receipt_rpc    = {receipt_rpc}")

    return 0 if status == 1 else 1


if __name__ == "__main__":
    raise SystemExit(main())
