#!/usr/bin/env python3
"""
Anchor v4.0 controlled evidence on Ethereum mainnet — EIP-4844 type-3 KZG blob TX.

Anchors:
  - All 8 v4.0 criterion artifacts (criteria 1-8, executed 2026-05-14)
  - AI-ME v3.1 aggregate report (12/12 PASS)
  - Fast Path v1.0 verification report (EVIDENCE_PASS 9/9)
  - v4.0 controlled evidence report
  - v4.0 external validation initiation record
  - Current git HEAD

Output: assurance/v4_0/V4_0_MAINNET_ANCHOR_RECEIPT.json

DRY_RUN=1 -> validates all crypto without broadcasting.
"""
import datetime, hashlib, json, os, subprocess, sys, time, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DRY  = os.environ.get("DRY_RUN") == "1"

RPCS = [
    "https://ethereum-rpc.publicnode.com",
    "https://eth.drpc.org",
    "https://1rpc.io/eth",
    "https://rpc.ankr.com/eth",
]

CRITERION_ARTIFACTS = {
    "V4_0_01_reproduction_kit":    "assurance/v4_0/evidence/V4_0_01_REPRODUCTION_KIT_ARTIFACT.json",
    "V4_0_02_security_review":     "assurance/v4_0/evidence/V4_0_02_SECURITY_REVIEW_ARTIFACT.json",
    "V4_0_03_cloud_deployment":    "assurance/v4_0/evidence/V4_0_03_CLOUD_DEPLOYMENT_ARTIFACT.json",
    "V4_0_04_hsm_signing":         "assurance/v4_0/evidence/V4_0_04_HSM_SIGNING_ARTIFACT.json",
    "V4_0_05_aem_reverification":  "assurance/v4_0/evidence/V4_0_05_AEM_REVERIFICATION_ARTIFACT.json",
    "V4_0_06_triple_anchor":       "assurance/v4_0/evidence/V4_0_06_TRIPLE_ANCHOR_ARTIFACT.json",
    "V4_0_07_fast_path_benchmark": "assurance/v4_0/evidence/V4_0_07_FAST_PATH_BENCHMARK_ARTIFACT.json",
    "V4_0_08_claim_review":        "assurance/v4_0/evidence/V4_0_08_CLAIM_REVIEW_ARTIFACT.json",
}

CORE_ARTIFACTS = {
    "ai_me_v3_1_aggregate":         "assurance/ai-me/v3_1/AI_ME_V3_1_AGGREGATE_REPORT.json",
    "fast_path_v1_0_verification":  "assurance/fast-path/v1/FAST_PATH_VERIFICATION_REPORT.json",
    "v4_0_controlled_evidence_rpt": "assurance/v4_0/V4_0_CONTROLLED_EVIDENCE_REPORT.json",
    "v4_0_initiation_record":       "assurance/v4_0/V4_0_EXTERNAL_VALIDATION_INITIATION_RECORD.json",
}

RECEIPT_OUT = ROOT / "assurance/v4_0/V4_0_MAINNET_ANCHOR_RECEIPT.json"
KZG_SETUP   = ROOT / "scripts/core/kzg_setup/trusted_setup.txt"


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rpc_call(method, params, timeout=20):
    body = json.dumps({"jsonrpc": "2.0", "id": 1, "method": method, "params": params}).encode()
    last = None
    for rpc in RPCS:
        try:
            req = urllib.request.Request(
                rpc, data=body,
                headers={"Content-Type": "application/json", "User-Agent": "curl/8.0"})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                res = json.loads(r.read())
            if "result" in res:
                return res["result"], rpc
            if "error" in res:
                last = f"{rpc}: {res['error']}"
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
        print("FAIL: ETHICBIT_PRIVATE_KEY not found")
        sys.exit(2)
    return priv if priv.startswith("0x") else "0x" + priv


def build_blob(payload_bytes: bytes) -> bytes:
    BLOB_SIZE, FE = 131072, 32
    blob = bytearray(BLOB_SIZE)
    for i, off in enumerate(range(0, len(payload_bytes), 31)):
        chunk = payload_bytes[off:off + 31]
        p = i * FE
        blob[p] = 0
        blob[p + 1:p + 1 + len(chunk)] = chunk
    return bytes(blob)


def build_payload() -> dict:
    criterion_hashes = {k: sha256_file(ROOT / v) for k, v in CRITERION_ARTIFACTS.items()}
    core_hashes      = {k: sha256_file(ROOT / v) for k, v in CORE_ARTIFACTS.items()}
    git_sha = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT).decode().strip()
    return {
        "schema":                    "ETHICBIT_AEM_V4_0_CONTROLLED_EVIDENCE_MAINNET_ANCHOR_V1",
        "anchor_scope":              "v4.0 controlled evidence execution — all 8 criteria — 2026-05-14",
        "constitutional_dependency": "EthicBit/CEMU/v3.7.0+",
        "criterion_artifact_hashes": criterion_hashes,
        "core_evidence_hashes":      core_hashes,
        "criteria_controlled_pass":  3,
        "criteria_pending_external": 5,
        "git_commit_sha":            git_sha,
        "ts_unix":                   int(time.time()),
        "non_claim": (
            "Ethereum mainnet anchor — timestamped integrity reference for v4.0 controlled "
            "evidence execution. Does not claim v4.0 validated, third-party reproduced, or "
            "production-ready. 5/8 criteria remain PENDING_EXTERNAL."
        ),
    }


def main():
    print("=" * 64)
    print("EthicBit / AEM-EVOLVE v4.0 Controlled Evidence Mainnet Anchor")
    print("=" * 64)

    payload_dict   = build_payload()
    payload_bytes  = json.dumps(payload_dict, sort_keys=True, separators=(",", ":")).encode()
    payload_sha256 = hashlib.sha256(payload_bytes).hexdigest()
    print(f"Payload built  ({len(payload_bytes)} bytes)")
    print(f"Payload SHA256: {payload_sha256}")
    print()
    print("Criterion artifact hashes:")
    for k, v in payload_dict["criterion_artifact_hashes"].items():
        print(f"  {k}: {v[:16]}...")
    print("Core evidence hashes:")
    for k, v in payload_dict["core_evidence_hashes"].items():
        print(f"  {k}: {v[:16]}...")
    print(f"git_commit: {payload_dict['git_commit_sha'][:16]}...")
    print()

    try:
        import ckzg
    except ImportError:
        print("FAIL: ckzg not installed — pip install ckzg")
        sys.exit(2)

    ts     = ckzg.load_trusted_setup(str(KZG_SETUP), 0)
    blob_b = build_blob(payload_bytes)
    commit = ckzg.blob_to_kzg_commitment(blob_b, ts)
    proof  = ckzg.compute_blob_kzg_proof(blob_b, commit, ts)
    if not ckzg.verify_blob_kzg_proof(blob_b, commit, proof, ts):
        print("FAIL: KZG proof verification failed")
        sys.exit(2)
    vh = b"\x01" + hashlib.sha256(commit).digest()[1:]
    print(f"KZG blob built  commitment={commit.hex()[:16]}...")
    print(f"versioned_hash: 0x{vh.hex()}")
    print()

    priv = load_priv_key()
    try:
        from eth_account import Account
    except ImportError:
        print("FAIL: eth_account not installed — pip install eth-account")
        sys.exit(2)

    wallet = Account.from_key(priv).address
    print(f"Wallet: {wallet}")

    nonce_hex, used_rpc = rpc_call("eth_getTransactionCount", [wallet, "latest"])
    nonce = int(nonce_hex, 16)
    print(f"RPC: {used_rpc}  nonce={nonce}")

    try:
        fh, _ = rpc_call("eth_feeHistory", ["0x5", "latest", []])
        base  = int(fh["baseFeePerGas"][-1], 16)
    except Exception:
        base = 5 * 10**9
    max_pri  = 2 * 10**9
    max_fee  = base * 3 + max_pri
    try:
        bbf, _    = rpc_call("eth_blobBaseFee", [])
        blob_base = int(bbf, 16) if isinstance(bbf, str) else 1
    except Exception:
        blob_base = 1
    max_blob_fee = max(blob_base * 5, 10**9)
    est_cost_eth = (max_fee * 21000 + max_blob_fee * 131072) / 1e18
    print(f"TX nonce={nonce}  maxFee={max_fee/1e9:.2f}gw  maxBlob={max_blob_fee/1e9:.4f}gw")
    print(f"Estimated cost: ~{est_cost_eth:.6f} ETH")
    print()

    tx = {
        "type": 3, "chainId": 1, "nonce": nonce,
        "to": wallet, "value": 0, "data": b"",
        "gas": 21000,
        "maxPriorityFeePerGas": max_pri,
        "maxFeePerGas":         max_fee,
        "maxFeePerBlobGas":     max_blob_fee,
        "blobVersionedHashes":  [vh],
    }
    signed  = Account.sign_transaction(tx, private_key=priv, blobs=[blob_b])
    raw     = getattr(signed, "raw_transaction", None) or signed.rawTransaction
    raw_hex = raw.hex() if isinstance(raw, bytes) else raw
    if not raw_hex.startswith("0x"):
        raw_hex = "0x" + raw_hex

    if DRY:
        print("=== DRY_RUN — TX not broadcast ===")
        print(f"  blob_size_bytes    : {len(blob_b)}")
        print(f"  payload_size_bytes : {len(payload_bytes)}")
        print(f"  versioned_hash     : 0x{vh.hex()}")
        print(f"  payload_sha256     : {payload_sha256}")
        print(f"  raw_tx_size_bytes  : {len(raw)}")
        print(f"  est_cost_mainnetETH: {est_cost_eth:.6f}")
        print()
        print("All cryptographic primitives validated. Re-run without DRY_RUN=1 to broadcast.")
        return

    print("Broadcasting TX to Ethereum mainnet...")
    tx_hash, used_rpc = rpc_call("eth_sendRawTransaction", [raw_hex])
    print(f"TX sent:  {tx_hash}")
    print(f"Via RPC:  {used_rpc}")
    print()

    print("Waiting for confirmation (up to 5 min)...")
    receipt_on_chain = None
    for i in range(60):
        time.sleep(5)
        try:
            r, _ = rpc_call("eth_getTransactionReceipt", [tx_hash])
            if r:
                receipt_on_chain = r
                break
        except Exception:
            pass
        if i % 6 == 0 and i > 0:
            print(f"  ...{(i*5)//60}m{(i*5)%60}s elapsed")
    if not receipt_on_chain:
        print("FAIL: not confirmed within 5 min")
        sys.exit(2)
    if int(receipt_on_chain["status"], 16) != 1:
        print(f"FAIL: TX reverted block={int(receipt_on_chain['blockNumber'],16)}")
        sys.exit(2)

    block_n = int(receipt_on_chain["blockNumber"], 16)
    print(f"CONFIRMED: block={block_n}")
    print()

    tx_data, _ = rpc_call("eth_getTransactionByHash", [tx_hash])

    anchor_receipt = {
        "schema_id":             "ETHICBIT_AEM_V4_0_CONTROLLED_EVIDENCE_MAINNET_ANCHOR_V1",
        "status":                "ONCHAIN_BLOB_ANCHOR_VERIFIED",
        "network":               "ethereum-mainnet",
        "chain_id":              1,
        "block_number":          block_n,
        "tx_hash":               tx_hash,
        "block_explorer_url":    f"https://etherscan.io/tx/{tx_hash}",
        "from_address":          tx_data.get("from", wallet),
        "to_address":            tx_data.get("to", wallet),
        "blob_versioned_hashes": ["0x" + vh.hex()],
        "timestamp_utc":         datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "anchored_at_unix":      payload_dict["ts_unix"],
        "verification_rpcs":     {"tx_lookup": used_rpc, "receipt_lookup": used_rpc},
        "payload":               payload_dict | {"payload_sha256": payload_sha256},
        "non_claim":             payload_dict["non_claim"],
    }

    RECEIPT_OUT.parent.mkdir(parents=True, exist_ok=True)
    RECEIPT_OUT.write_text(json.dumps(anchor_receipt, indent=2))
    print(f"Receipt written: {RECEIPT_OUT}")
    print()
    print("=" * 64)
    print("MAINNET ANCHOR COMPLETE")
    print("=" * 64)
    print(f"  tx_hash       : {tx_hash}")
    print(f"  block         : {block_n}")
    print(f"  network       : ethereum-mainnet")
    print(f"  explorer      : https://etherscan.io/tx/{tx_hash}")
    print(f"  schema        : ETHICBIT_AEM_V4_0_CONTROLLED_EVIDENCE_MAINNET_ANCHOR_V1")
    print(f"  git_commit    : {payload_dict['git_commit_sha'][:16]}...")
    print(f"  criteria_pass : 3/8 CONTROLLED_PASS  5/8 PENDING_EXTERNAL")


if __name__ == "__main__":
    main()
