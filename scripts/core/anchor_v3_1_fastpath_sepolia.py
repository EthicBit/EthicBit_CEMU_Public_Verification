#!/usr/bin/env python3
"""
Anchor v3.1 + Fast Path v1.0 evidence on Sepolia — EIP-4844 type-3 KZG blob TX.

Anchors:
  - AI-ME v3.1 aggregate report (12/12 PASS)
  - Fast Path v1.0 verification report (EVIDENCE_PASS 9/9)
  - v4.0 controlled evidence report (CONTROLLED_EVIDENCE_PARTIAL 3/8)
  - 12 individual AI-ME v3.1 artifact hashes
  - Current git HEAD

Output: assurance/v4_0/V4_0_SEPOLIA_ANCHOR_RECEIPT.json

Non-claim: Sepolia testnet anchor — not Ethereum mainnet.
           Timestamped integrity reference only — not certification,
           regulatory approval, or production readiness.

DRY_RUN=1 -> validates all crypto without broadcasting.
"""
import hashlib, json, os, subprocess, sys, time, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DRY  = os.environ.get("DRY_RUN") == "1"

RPCS = [
    "https://ethereum-sepolia-rpc.publicnode.com",
    "https://sepolia.drpc.org",
    "https://1rpc.io/sepolia",
    "https://gateway.tenderly.co/public/sepolia",
]

ARTIFACTS = {
    "ai_me_v3_1_aggregate":        "assurance/ai-me/v3_1/AI_ME_V3_1_AGGREGATE_REPORT.json",
    "fast_path_v1_0_verification": "assurance/fast-path/v1/FAST_PATH_VERIFICATION_REPORT.json",
    "v4_0_controlled_evidence":    "assurance/v4_0/V4_0_CONTROLLED_EVIDENCE_REPORT.json",
}

AI_ME_RECEIPTS_DIR = ROOT / "assurance/ai-me/v3_1"
RECEIPT_OUT = ROOT / "assurance/v4_0/V4_0_SEPOLIA_ANCHOR_RECEIPT.json"
KZG_SETUP   = ROOT / "scripts/core/kzg_setup/trusted_setup.txt"


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rpc_call(method, params, timeout=20):
    body = json.dumps({"jsonrpc":"2.0","id":1,"method":method,"params":params}).encode()
    last = None
    for rpc in RPCS:
        try:
            req = urllib.request.Request(rpc, data=body,
                headers={"Content-Type":"application/json","User-Agent":"curl/8.0"})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                res = json.loads(r.read())
            if "result" in res: return res["result"], rpc
            if "error" in res: last = f"{rpc}: {res['error']}"
        except Exception as e:
            last = f"{rpc}: {str(e)[:80]}"
    raise RuntimeError(f"All RPCs failed for {method}: {last}")


def load_priv_key() -> str:
    priv = os.environ.get("ETHICBIT_PRIVATE_KEY", "")
    if not priv:
        env_file = ROOT / ".env"
        if env_file.exists():
            for ln in env_file.read_text().splitlines():
                s = ln.strip()
                if s.startswith("ETHICBIT_PRIVATE_KEY="):
                    priv = s.split("=", 1)[1].strip().strip('"').strip("'")
                    break
    if not priv:
        print("FAIL: ETHICBIT_PRIVATE_KEY not found"); sys.exit(2)
    return priv if priv.startswith("0x") else "0x" + priv


def build_payload() -> dict:
    hashes = {}
    for name, rel_path in ARTIFACTS.items():
        p = ROOT / rel_path
        hashes[f"{name}_sha256"] = sha256_file(p)
        print(f"  [{name}]: {hashes[f'{name}_sha256'][:16]}...")

    # 12 AI-ME v3.1 artifact hashes
    ai_me_artifact_hashes = {}
    receipts = sorted(AI_ME_RECEIPTS_DIR.glob("receipt_AI-ME-*.json"))
    for r_path in receipts:
        receipt = json.loads(r_path.read_text())
        gate_id = receipt.get("gate_id", r_path.stem)
        artifact_path = ROOT / receipt.get("artifact_path", "")
        if artifact_path.exists():
            ai_me_artifact_hashes[gate_id] = sha256_file(artifact_path)
    print(f"  AI-ME v3.1 artifact hashes: {len(ai_me_artifact_hashes)}/12")

    git_sha = subprocess.check_output(["git","rev-parse","HEAD"], cwd=str(ROOT)).decode().strip()

    return {
        "schema": "ETHICBIT_AEM_V3_1_FASTPATH_V1_0_ANCHOR_V1",
        "anchor_scope": "AI-ME v3.1 PASS (12/12) + Fast Path v1.0 EVIDENCE_PASS (9/9) + v4.0 CONTROLLED_EVIDENCE_PARTIAL (3/8)",
        "constitutional_dependency": "EthicBit/CEMU/v3.7.0+",
        **hashes,
        "ai_me_v3_1_artifact_hashes": ai_me_artifact_hashes,
        "git_commit_sha": git_sha,
        "ts_unix": int(time.time()),
        "network": "sepolia-testnet",
        "chain_id": 11155111,
        "non_claim": (
            "Sepolia testnet anchor — not Ethereum mainnet. "
            "Timestamped integrity reference only. "
            "Not certification, regulatory approval, production readiness, or mainnet anchor."
        ),
    }


def build_blob(payload_bytes: bytes) -> bytes:
    BLOB_SIZE, FE = 131072, 32
    blob = bytearray(BLOB_SIZE)
    for i, off in enumerate(range(0, len(payload_bytes), 31)):
        chunk = payload_bytes[off:off+31]
        p = i * FE
        blob[p] = 0
        blob[p+1:p+1+len(chunk)] = chunk
    return bytes(blob)


def main():
    print("=== AEM v3.1 + Fast Path v1.0 — Sepolia Anchor ===")
    print(f"Network: Sepolia testnet (chain_id=11155111)")
    print(f"DRY_RUN: {DRY}")
    print()

    priv = load_priv_key()
    from eth_account import Account
    import ckzg

    acct = Account.from_key(priv)
    wallet = acct.address
    print(f"Wallet: {wallet}")
    print()

    # Build payload
    print("Computing evidence hashes...")
    payload_dict = build_payload()
    payload_bytes = json.dumps(payload_dict, sort_keys=True,
                               separators=(",",":"), ensure_ascii=False).encode()
    payload_sha256 = hashlib.sha256(payload_bytes).hexdigest()
    print(f"Payload: {len(payload_bytes)}B  sha256={payload_sha256[:16]}...")
    print()

    # KZG
    print("Loading KZG trusted setup...")
    try:
        ts = ckzg.load_trusted_setup(str(KZG_SETUP), 0)
    except TypeError:
        ts = ckzg.load_trusted_setup(str(KZG_SETUP))
    print("KZG setup loaded.")

    blob_b    = build_blob(payload_bytes)
    commit    = ckzg.blob_to_kzg_commitment(blob_b, ts)
    proof     = ckzg.compute_blob_kzg_proof(blob_b, commit, ts)
    if not ckzg.verify_blob_kzg_proof(blob_b, commit, proof, ts):
        print("FAIL: KZG self-verify"); sys.exit(2)
    vh = bytes([0x01]) + hashlib.sha256(commit).digest()[1:]
    print(f"KZG OK — versioned_hash=0x{vh.hex()[:32]}...")
    print()

    # Fee estimation
    nonce_hex, _ = rpc_call("eth_getTransactionCount", [wallet, "latest"])
    nonce = int(nonce_hex, 16)
    try:
        fh, _ = rpc_call("eth_feeHistory", [hex(4), "latest", [50]])
        base = int(fh["baseFeePerGas"][-1], 16)
    except Exception:
        base = 5 * 10**9
    max_pri     = 2 * 10**9
    max_fee     = base * 3 + max_pri
    try:
        bbf, _   = rpc_call("eth_blobBaseFee", [])
        blob_base = int(bbf, 16) if isinstance(bbf, str) else 1
    except Exception:
        blob_base = 1
    max_blob_fee = max(blob_base * 5, 10**9)
    est_cost_eth = (max_fee * 25000 + max_blob_fee * 131072) / 10**18
    print(f"TX nonce={nonce}  maxFee={max_fee/1e9:.2f}gw  maxBlob={max_blob_fee/1e9:.2f}gw")
    print(f"Estimated cost: ~{est_cost_eth:.6f} SepoliaETH")
    print()

    tx = {
        "type": 3, "chainId": 11155111, "nonce": nonce,
        "to": wallet, "value": 0, "data": b"",
        "gas": 25000,
        "maxPriorityFeePerGas": max_pri,
        "maxFeePerGas": max_fee,
        "maxFeePerBlobGas": max_blob_fee,
        "blobVersionedHashes": [vh],
    }
    signed = Account.sign_transaction(tx, private_key=priv, blobs=[blob_b])
    raw    = getattr(signed, "raw_transaction", None) or signed.rawTransaction
    raw_hex = raw.hex() if isinstance(raw, bytes) else raw
    if not raw_hex.startswith("0x"): raw_hex = "0x" + raw_hex

    if DRY:
        print("=== DRY_RUN — TX not broadcast ===")
        print(f"  blob_size_bytes    : {len(blob_b)}")
        print(f"  payload_size_bytes : {len(payload_bytes)}")
        print(f"  versioned_hash     : 0x{vh.hex()}")
        print(f"  payload_sha256     : {payload_sha256}")
        print(f"  raw_tx_size_bytes  : {len(raw)}")
        print(f"  est_cost_sepoliaETH: {est_cost_eth:.6f}")
        print()
        print("All cryptographic primitives validated. Re-run without DRY_RUN=1 to broadcast.")
        return

    # Broadcast
    print("Broadcasting TX...")
    tx_hash, used_rpc = rpc_call("eth_sendRawTransaction", [raw_hex])
    print(f"TX sent:  {tx_hash}")
    print(f"Via RPC:  {used_rpc}")
    print()

    # Wait for confirmation
    print("Waiting for confirmation (up to 5 min)...")
    receipt_on_chain = None
    for i in range(60):
        time.sleep(5)
        try:
            r, _ = rpc_call("eth_getTransactionReceipt", [tx_hash])
            if r:
                receipt_on_chain = r; break
        except Exception:
            pass
        if i % 6 == 0 and i > 0:
            print(f"  ...{(i*5)//60}m{(i*5)%60}s elapsed")
    if not receipt_on_chain:
        print("FAIL: not confirmed within 5 min"); sys.exit(2)
    if int(receipt_on_chain["status"], 16) != 1:
        print(f"FAIL: TX reverted block={int(receipt_on_chain['blockNumber'],16)}"); sys.exit(2)

    block_n = int(receipt_on_chain["blockNumber"], 16)
    print(f"CONFIRMED: block={block_n}")
    print()

    # Get tx details for receipt
    tx_data, _ = rpc_call("eth_getTransactionByHash", [tx_hash])

    # Build receipt
    anchor_receipt = {
        "schema_id":            "ETHICBIT_AEM_V3_1_FASTPATH_V1_0_SEPOLIA_ANCHOR_V1",
        "status":               "ONCHAIN_BLOB_ANCHOR_VERIFIED",
        "network":              "sepolia-testnet",
        "chain_id":             11155111,
        "block_number":         block_n,
        "tx_hash":              tx_hash,
        "from_address":         tx_data.get("from", wallet),
        "to_address":           tx_data.get("to", wallet),
        "blob_versioned_hashes": ["0x" + vh.hex()],
        "timestamp_utc":        __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat(),
        "anchored_at_unix":     payload_dict["ts_unix"],
        "verification_rpcs":    {"tx_lookup": used_rpc, "receipt_lookup": used_rpc},
        "payload": {
            "schema":                        payload_dict["schema"],
            "anchor_scope":                  payload_dict["anchor_scope"],
            "constitutional_dependency":     payload_dict["constitutional_dependency"],
            "ai_me_v3_1_aggregate_sha256":   payload_dict["ai_me_v3_1_aggregate_sha256"],
            "fast_path_v1_0_verification_sha256": payload_dict["fast_path_v1_0_verification_sha256"],
            "v4_0_controlled_evidence_sha256": payload_dict["v4_0_controlled_evidence_sha256"],
            "ai_me_v3_1_artifact_hashes":    payload_dict["ai_me_v3_1_artifact_hashes"],
            "git_commit_sha":                payload_dict["git_commit_sha"],
            "ts_unix":                       payload_dict["ts_unix"],
            "payload_sha256":                payload_sha256,
        },
        "non_claim": payload_dict["non_claim"],
    }

    RECEIPT_OUT.parent.mkdir(parents=True, exist_ok=True)
    RECEIPT_OUT.write_text(json.dumps(anchor_receipt, indent=2))
    print(f"Receipt written: {RECEIPT_OUT}")
    print()
    print("=" * 64)
    print("ANCHOR COMPLETE")
    print("=" * 64)
    print(f"  tx_hash       : {tx_hash}")
    print(f"  block         : {block_n}")
    print(f"  network       : sepolia-testnet")
    print(f"  schema        : ETHICBIT_AEM_V3_1_FASTPATH_V1_0_SEPOLIA_ANCHOR_V1")
    print(f"  git_commit    : {payload_dict['git_commit_sha'][:16]}...")
    print(f"  anchored scope: {payload_dict['anchor_scope']}")


if __name__ == "__main__":
    main()
