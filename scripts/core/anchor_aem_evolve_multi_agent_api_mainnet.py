#!/usr/bin/env python3
"""
Anchor AEM-EVOLVE Multi-Agent Governance API demo manifest on Ethereum mainnet.

Safety controls:
  - DRY_RUN=1  prints payload and validates network, never broadcasts.
  - BROADCAST=1 is required for a real broadcast.

Env vars:
  DRY_RUN=1
  BROADCAST=1
  ETHICBIT_MAINNET_RPC_URL=https://...
  ETH_RPC_URL=https://...                           # fallback alias
  ETHICBIT_PRIVATE_KEY=0x...
  ETH_PRIVATE_KEY=0x...                             # fallback alias
  ETHICBIT_AEM_EVOLVE_MULTI_AGENT_EXPECTED_SHA256=<hex64>  # optional override
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

MANIFEST_PATH = (
    ROOT / "assurance" / "evolve-multi-agent" / "AEM_EVOLVE_MULTI_AGENT_API_MANIFEST.json"
)
HASH_RECORD_PATH = (
    ROOT / "assurance" / "evolve-multi-agent" / "AEM_EVOLVE_MULTI_AGENT_API_HASH_RECORD.txt"
)
ANCHOR_RECEIPT_PATH = (
    ROOT
    / "assurance"
    / "evolve-multi-agent"
    / "AEM_EVOLVE_MULTI_AGENT_API_ANCHOR_RECEIPT.json"
)

# Computed from the manifest at PR 1 merge commit 95431b34
DEFAULT_EXPECTED_CANONICAL_SHA = (
    "dddc7a62314392006daa245001466940ac3a3f49c722a01668114f329c1b5d59"
)

SOURCE_COMMIT = "95431b34"
DEMO_VERSION = "0.3.1-demo"
NETWORK = "ethereum-mainnet"
CHAIN_ID = 1
SCHEMA_ID = "AEM_EVOLVE_MULTI_AGENT_API_MAINNET_ANCHOR_PAYLOAD_V0_3_1_DEMO"
RECEIPT_SCHEMA_ID = "AEM_EVOLVE_MULTI_AGENT_API_MAINNET_ANCHOR_RECEIPT_V0_3_1_DEMO"


def _now_utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _sha256_file(path: Path) -> str:
    return _sha256_bytes(path.read_bytes())


def _sha256_canonical_json(path: Path) -> str:
    obj = json.loads(path.read_text(encoding="utf-8"))
    payload = json.dumps(
        obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False
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
                result = json.loads(resp.read())
            if "result" in result:
                return result["result"], rpc
            last_error = f"{rpc}: {result.get('error')}"
        except Exception as exc:  # noqa: BLE001
            last_error = f"{rpc}: {str(exc)[:160]}"
    raise RuntimeError(f"all RPCs failed for {method}: {last_error}")


def _read_private_key() -> str:
    value = os.environ.get("ETHICBIT_PRIVATE_KEY", "").strip() or os.environ.get(
        "ETH_PRIVATE_KEY", ""
    ).strip()
    if not value:
        raise RuntimeError("missing ETHICBIT_PRIVATE_KEY (or ETH_PRIVATE_KEY)")
    key = value[2:] if value.startswith("0x") else value
    if not re.fullmatch(r"[0-9a-fA-F]{64}", key):
        raise RuntimeError(f"private_key must contain exactly 64 hex digits (got {len(key)})")
    return "0x" + key


def _expected_canonical_hash() -> str:
    env_override = os.environ.get(
        "ETHICBIT_AEM_EVOLVE_MULTI_AGENT_EXPECTED_SHA256", ""
    ).strip().lower()
    if env_override:
        return env_override
    return DEFAULT_EXPECTED_CANONICAL_SHA


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _build_payload(
    manifest_canonical_sha: str,
    manifest_file_sha: str,
    manifest_obj: dict,
) -> dict:
    return {
        "schema_id": SCHEMA_ID,
        "artifact": "AEM-EVOLVE Multi-Agent Governance API",
        "version": DEMO_VERSION,
        "current_milestone": "PR 2 - Demo Mainnet Anchor",
        "current_status": "TECHNICAL_DEMONSTRATION_PACKAGE",
        "claim": (
            "AEM-EVOLVE Multi-Agent Governance API v0.3.1-demo manifest anchored on "
            "Ethereum mainnet as public timestamped integrity reference."
        ),
        "source_commit": SOURCE_COMMIT,
        "manifest_relative_path": str(MANIFEST_PATH.relative_to(ROOT)),
        "hash_record_relative_path": str(HASH_RECORD_PATH.relative_to(ROOT)),
        "manifest_canonical_sha256": manifest_canonical_sha,
        "manifest_file_sha256": manifest_file_sha,
        "manifest_canonicalization": "json_sort_keys_no_whitespace_utf8",
        "manifest_hash_algorithm": "SHA-256",
        "files_count": len(manifest_obj.get("files", [])),
        "prior_anchor_status": manifest_obj.get("anchor_status"),
        "prior_signature_status": manifest_obj.get("signature_status"),
        "non_claims": {
            "certification_claimed": False,
            "approval_claimed": False,
            "independent_reproduction_claimed": False,
            "production_ready_claimed": False,
            "cryptographically_signed_receipts": False,
            "regulatory_approved": False,
            "clinical_or_diagnostic": False,
            "externally_certified": False,
            "production_authentication_or_authorization": False,
            "tamper_proof_audit_trail": False,
            "production_grade_database_storage": False,
        },
        "ts_unix": int(time.time()),
    }


def main() -> int:
    dry_run = os.environ.get("DRY_RUN") == "1"
    broadcast = os.environ.get("BROADCAST") == "1"
    rpcs = _rpc_endpoints()

    if not MANIFEST_PATH.exists():
        print(f"ERROR: manifest not found: {MANIFEST_PATH}", file=sys.stderr)
        return 1

    manifest_obj = _read_json(MANIFEST_PATH)
    manifest_canonical_sha = _sha256_canonical_json(MANIFEST_PATH)
    manifest_file_sha = _sha256_file(MANIFEST_PATH)
    expected_sha = _expected_canonical_hash()

    print("=== AEM-EVOLVE MULTI-AGENT API MANIFEST HASH CHECK ===")
    print(f"manifest_path      = {MANIFEST_PATH}")
    print(f"canonical_sha256   = {manifest_canonical_sha}")
    print(f"file_sha256        = {manifest_file_sha}")
    print(f"expected_canonical = {expected_sha}")

    if manifest_canonical_sha.lower() != expected_sha.lower():
        print(
            "ERROR: manifest canonical hash does not match expected hash record.",
            file=sys.stderr,
        )
        return 1

    payload = _build_payload(manifest_canonical_sha, manifest_file_sha, manifest_obj)
    payload_bytes = json.dumps(
        payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    payload_sha = _sha256_bytes(payload_bytes)

    print("\n=== AEM-EVOLVE MULTI-AGENT API ANCHOR PAYLOAD ===")
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
        print(f"existing anchor status={existing_status} tx={existing_tx}")
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
    print(f"max_fee_gwei   = {max_fee / 1e9:.3f}")
    print(f"max_pri_gwei   = {max_priority / 1e9:.3f}")

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
            "ONCHAIN_AEM_EVOLVE_MULTI_AGENT_API_DEMO_ANCHOR_VERIFIED"
            if status == 1
            else "ONCHAIN_AEM_EVOLVE_MULTI_AGENT_API_DEMO_ANCHOR_FAILED"
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
        "demo_manifest": {
            "manifest_path": str(MANIFEST_PATH.relative_to(ROOT)),
            "manifest_canonical_sha256": manifest_canonical_sha,
            "manifest_file_sha256": manifest_file_sha,
            "hash_algorithm": "SHA-256",
            "canonicalization": "json_sort_keys_no_whitespace_utf8",
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
