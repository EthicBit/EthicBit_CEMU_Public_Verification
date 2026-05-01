#!/usr/bin/env python3
"""Materialize AEM V1.1 mainnet receipt from an already-confirmed tx hash.

Usage:
  python3 scripts/core/write_aem_mainnet_receipt_from_tx.py \
    --tx-hash 0x... \
    --freeze-pdf-sha256 <hex64>
"""
import argparse
import hashlib
import json
import subprocess
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_RPCS = [
    "https://ethereum-rpc.publicnode.com",
    "https://1rpc.io/eth",
    "https://eth.llamarpc.com",
]


def rpc_call(rpcs, method, params, timeout=25):
    body = json.dumps({"jsonrpc": "2.0", "id": 1, "method": method, "params": params}).encode()
    last = None
    for rpc in rpcs:
        try:
            req = urllib.request.Request(
                rpc,
                data=body,
                headers={"Content-Type": "application/json", "User-Agent": "curl/8.0"},
            )
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                out = json.loads(resp.read())
            if "result" in out:
                return out["result"], rpc
            last = f"{rpc}: {out.get('error')}"
        except Exception as exc:
            last = f"{rpc}: {str(exc)[:120]}"
    raise RuntimeError(f"all RPCs failed for {method}: {last}")


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sha256_canonical_json(path: Path) -> str:
    payload = json.loads(path.read_text())
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def to_iso(ts: int) -> str:
    return datetime.fromtimestamp(ts, tz=timezone.utc).isoformat()


def main():
    ap = argparse.ArgumentParser(description="Write AEM V1.1 mainnet receipt from tx hash")
    ap.add_argument("--tx-hash", required=True, help="Mainnet tx hash")
    ap.add_argument("--freeze-pdf-sha256", required=True, help="Freeze PDF SHA-256")
    ap.add_argument("--repo-commit-sha", default="", help="Repo commit SHA included in anchored payload")
    ap.add_argument("--signer-identity", default="ETHICBIT_MAIN_SIGNER", help="Signer identity label")
    ap.add_argument("--rpc", action="append", default=[], help="RPC endpoint (can repeat)")
    args = ap.parse_args()

    tx_hash = args.tx_hash.strip()
    if not tx_hash.startswith("0x") or len(tx_hash) != 66:
        raise SystemExit("Invalid tx hash format")

    rpcs = args.rpc + DEFAULT_RPCS
    tx, tx_rpc = rpc_call(rpcs, "eth_getTransactionByHash", [tx_hash])
    if not tx:
        raise SystemExit("Transaction not found")
    rcpt, rcpt_rpc = rpc_call(rpcs, "eth_getTransactionReceipt", [tx_hash])
    if not rcpt:
        raise SystemExit("Receipt not found")
    block, blk_rpc = rpc_call(rpcs, "eth_getBlockByNumber", [rcpt["blockNumber"], False])
    if not block:
        raise SystemExit("Block not found")

    if int(rcpt.get("status", "0x0"), 16) != 1:
        raise SystemExit("Transaction is not successful")

    canonical_sha = sha256_file(ROOT / "docs" / "AGENTE_ETICO_MECANICO_V1_1.md")
    thesis_sha = sha256_file(ROOT / "docs" / "AEM_STRATEGIC_THESIS_FOR_AGENTIC_AI_V1_1.md")
    system_sha = sha256_canonical_json(ROOT / "results" / "master_closure_report.json")
    repo_commit_sha = args.repo_commit_sha.strip()
    if not repo_commit_sha:
        try:
            repo_commit_sha = (
                subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=str(ROOT))
                .decode()
                .strip()
            )
        except Exception:
            repo_commit_sha = None

    block_number = int(rcpt["blockNumber"], 16)
    ts_unix = int(block["timestamp"], 16)
    gas_used = int(rcpt.get("gasUsed", "0x0"), 16)
    eff_gas = int(rcpt.get("effectiveGasPrice", "0x0"), 16)
    fee_wei = gas_used * eff_gas

    receipt_payload = {
        "schema_id": "ETHICBIT_AEM_V1_1_MAINNET_ANCHOR_RECEIPT_V1",
        "status": "ONCHAIN_BLOB_ANCHOR_VERIFIED",
        "network": "ethereum-mainnet",
        "chain_id": 1,
        "tx_hash": tx_hash,
        "block_number": block_number,
        "timestamp_utc": to_iso(ts_unix),
        "block_explorer_url": f"https://etherscan.io/tx/{tx_hash}",
        "from_address": tx.get("from"),
        "to_address": tx.get("to"),
        "blob_versioned_hashes": tx.get("blobVersionedHashes", []),
        "gas_used": gas_used,
        "effective_gas_price_wei": eff_gas,
        "fee_paid_wei": fee_wei,
        "fee_paid_eth": fee_wei / 10**18,
        "payload": {
            "canonical_sha256": canonical_sha,
            "thesis_sha256": thesis_sha,
            "system_state_sha256": system_sha,
            "freeze_pdf_sha256": args.freeze_pdf_sha256.lower(),
            "repo_commit_sha": repo_commit_sha,
            "signer_identity": args.signer_identity,
            "signer_address": tx.get("from"),
            "ts_unix": ts_unix,
        },
        "verification_rpcs": {
            "tx_lookup": tx_rpc,
            "receipt_lookup": rcpt_rpc,
            "block_lookup": blk_rpc,
        },
    }

    out_doc = ROOT / "docs" / "anchors" / "AEM_V1_1_MAINNET_ANCHOR_RECEIPT.json"
    out_results = ROOT / "results" / "aem_v1_1_mainnet_anchor_report.json"
    out_doc.write_text(json.dumps(receipt_payload, indent=2, sort_keys=True))
    out_results.write_text(json.dumps(receipt_payload, indent=2, sort_keys=True))

    print("RECEIPT_WRITTEN=" + str(out_doc))
    print("REPORT_WRITTEN=" + str(out_results))
    print("TX_HASH=" + tx_hash)
    print("BLOCK_NUMBER=" + str(block_number))
    print("BLOB_HASHES=" + json.dumps(receipt_payload["blob_versioned_hashes"]))


if __name__ == "__main__":
    main()
