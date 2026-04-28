#!/usr/bin/env python3
"""STAGE 3: cross-verify the on-chain anchor against public RPCs.

Reads tx_hash from kzg_blob_anchor_report.json and queries public Sepolia
RPCs to confirm the TX exists with matching properties:
  - type == 0x3 (EIP-4844 blob)
  - from == anchor.from_address
  - blockNumber == anchor.block_number
  - blobVersionedHashes == anchor.blob_versioned_hashes
  - receipt.status == 1 (success)

Closes the gap of trusting the local JSON. If anchor JSON was tampered
with (e.g., replaced tx_hash with a fake one), public RPCs would either
fail to find the TX or report different data, triggering FAIL.

Exit codes:
  0 : at least one RPC confirmed all properties match
  1 : at least one RPC found the TX but reports MISMATCH (tampering)
  2 : no RPC could reach the TX (network issue or non-existent TX)
"""
import json, sys, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
anchor_path = ROOT / "results" / "kzg_blob_anchor_report.json"
if not anchor_path.exists():
    print(f"FAIL: missing {anchor_path}"); sys.exit(2)

anchor = json.loads(anchor_path.read_text())
tx_hash = anchor["tx_hash"]
expected = {
    "type": "0x3",
    "from": anchor["from_address"].lower(),
    "block_number": int(anchor["block_number"]),
    "vhashes": set(h.lower() for h in anchor["blob_versioned_hashes"]),
}

RPCS = [
    "https://sepolia.drpc.org",
    "https://1rpc.io/sepolia",
    "https://gateway.tenderly.co/public/sepolia",
    "https://ethereum-sepolia-rpc.publicnode.com",
]

def rpc(url, method, params, timeout=15):
    body = json.dumps({"jsonrpc":"2.0","id":1,"method":method,"params":params}).encode()
    req = urllib.request.Request(url, data=body,
        headers={"Content-Type":"application/json","User-Agent":"curl/8.0"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        res = json.loads(r.read())
    if "error" in res: raise RuntimeError(str(res["error"]))
    return res["result"]

print(f"[ONCHAIN] cross-verifying {tx_hash}")
print(f"[ONCHAIN] expected: type=0x3 from={expected['from'][:18]}... block={expected['block_number']} vhashes={len(expected['vhashes'])}")

errors = []
for url in RPCS:
    try:
        tx = rpc(url, "eth_getTransactionByHash", [tx_hash])
        if tx is None:
            errors.append(f"{url}: tx not found"); continue
        receipt = rpc(url, "eth_getTransactionReceipt", [tx_hash])
        if receipt is None:
            errors.append(f"{url}: receipt not found"); continue
        # cruza-verificar propiedades
        mismatches = []
        if tx.get("type") != expected["type"]:
            mismatches.append(f"type {tx.get('type')!r} != {expected['type']!r}")
        if (tx.get("from") or "").lower() != expected["from"]:
            mismatches.append(f"from {tx.get('from')!r} != {expected['from']!r}")
        bn_onchain = int(tx.get("blockNumber","0x0"), 16)
        if bn_onchain != expected["block_number"]:
            mismatches.append(f"block {bn_onchain} != {expected['block_number']}")
        vh_onchain = set((h or "").lower() for h in (tx.get("blobVersionedHashes") or []))
        if vh_onchain != expected["vhashes"]:
            mismatches.append(f"vhashes {vh_onchain} != {expected['vhashes']}")
        status = int(receipt.get("status","0x0"), 16)
        if status != 1:
            mismatches.append(f"receipt.status={status}, expected 1")
        if mismatches:
            print(f"FAIL: {url} reports MISMATCH (tampering or wrong data?):")
            for m in mismatches: print(f"  - {m}")
            sys.exit(1)
        # PASS
        print(f"\n[ONCHAIN] confirmed via {url}")
        print(f"  type      : 0x3 (EIP-4844 blob)")
        print(f"  from      : {tx.get('from')}")
        print(f"  block     : {bn_onchain}")
        print(f"  vhashes   : {len(vh_onchain)} matching")
        print(f"  receipt   : status=success")
        print("ONCHAIN_CROSS_VERIFICATION=PASS")
        sys.exit(0)
    except Exception as e:
        errors.append(f"{url}: {str(e)[:80]}")
        continue

print("FAIL: no RPC could confirm the on-chain anchor")
for e in errors: print(f"  - {e}")
sys.exit(2)
