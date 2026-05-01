#!/usr/bin/env python3
"""Anchor AEM V1.1 payload on Ethereum mainnet using EIP-4844 blob.

This script is intentionally separate from Sepolia tooling.

Environment variables:
  DRY_RUN=1                                  Validate full crypto flow, do not broadcast.
  ETHICBIT_PRIVATE_KEY=0x...                 Signer private key.
  ETHICBIT_MAINNET_RPC_URL=https://...       Optional preferred RPC endpoint.
  ETHICBIT_AEM_CANONICAL_SHA256=<hex64>      Optional override.
  ETHICBIT_AEM_THESIS_SHA256=<hex64>         Optional override.
  ETHICBIT_AEM_SYSTEM_STATE_SHA256=<hex64>   Optional override.
  ETHICBIT_AEM_FREEZE_PDF_SHA256=<hex64>     Optional optional inclusion.
  ETHICBIT_AEM_SIGNER_IDENTITY=<string>      Optional signer identity label.
"""
import hashlib
import json
import os
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

from eth_account import Account
from eth_account.messages import encode_defunct
import ckzg

ROOT = Path(__file__).resolve().parents[2]
DRY = os.environ.get("DRY_RUN") == "1"


def _read_private_key() -> str:
    priv = os.environ.get("ETHICBIT_PRIVATE_KEY")
    if not priv:
        env_file = ROOT / ".env"
        if env_file.exists():
            for line in env_file.read_text().splitlines():
                s = line.strip()
                if s.startswith("ETHICBIT_PRIVATE_KEY="):
                    priv = s.split("=", 1)[1].strip().strip('"').strip("'")
                    break
    if not priv:
        print("FAIL: missing ETHICBIT_PRIVATE_KEY")
        sys.exit(2)
    if not priv.startswith("0x"):
        priv = "0x" + priv
    return priv


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _sha256_canonical_json(path: Path) -> str:
    payload = json.loads(path.read_text())
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _resolve_aem_hashes() -> dict:
    canonical_sha = os.environ.get("ETHICBIT_AEM_CANONICAL_SHA256")
    thesis_sha = os.environ.get("ETHICBIT_AEM_THESIS_SHA256")
    system_sha = os.environ.get("ETHICBIT_AEM_SYSTEM_STATE_SHA256")
    freeze_pdf_sha = os.environ.get("ETHICBIT_AEM_FREEZE_PDF_SHA256")

    canonical_file = ROOT / "docs" / "AGENTE_ETICO_MECANICO_V1_1.md"
    thesis_file = ROOT / "docs" / "AEM_STRATEGIC_THESIS_FOR_AGENTIC_AI_V1_1.md"
    system_file = ROOT / "results" / "master_closure_report.json"

    if not canonical_sha:
        if not canonical_file.exists():
            print("FAIL: missing canonical file and ETHICBIT_AEM_CANONICAL_SHA256 not set")
            sys.exit(2)
        canonical_sha = _sha256_file(canonical_file)
    if not thesis_sha:
        if not thesis_file.exists():
            print("FAIL: missing thesis file and ETHICBIT_AEM_THESIS_SHA256 not set")
            sys.exit(2)
        thesis_sha = _sha256_file(thesis_file)
    if not system_sha:
        if not system_file.exists():
            print("FAIL: missing system state file and ETHICBIT_AEM_SYSTEM_STATE_SHA256 not set")
            sys.exit(2)
        system_sha = _sha256_canonical_json(system_file)

    return {
        "canonical_sha256": canonical_sha.lower(),
        "thesis_sha256": thesis_sha.lower(),
        "system_state_sha256": system_sha.lower(),
        "freeze_pdf_sha256": freeze_pdf_sha.lower() if freeze_pdf_sha else None,
    }


def _rpc_list() -> list[str]:
    preferred = os.environ.get("ETHICBIT_MAINNET_RPC_URL", "").strip()
    base = [
        "https://eth.llamarpc.com",
        "https://ethereum-rpc.publicnode.com",
        "https://1rpc.io/eth",
        "https://rpc.ankr.com/eth",
    ]
    if preferred:
        return [preferred] + [x for x in base if x != preferred]
    return base


RPCS = _rpc_list()


def rpc_call(method, params, timeout=25):
    body = json.dumps({"jsonrpc": "2.0", "id": 1, "method": method, "params": params}).encode()
    last = None
    for rpc in RPCS:
        try:
            req = urllib.request.Request(
                rpc,
                data=body,
                headers={"Content-Type": "application/json", "User-Agent": "curl/8.0"},
            )
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                res = json.loads(resp.read())
            if "result" in res:
                return res["result"], rpc
            if "error" in res:
                last = f"{rpc}: {res['error']}"
        except Exception as exc:
            last = f"{rpc}: {str(exc)[:120]}"
    raise RuntimeError(f"all RPCs failed for {method}: {last}")


def _load_kzg_setup():
    setup = ROOT / "scripts" / "core" / "kzg_setup" / "trusted_setup.txt"
    setup.parent.mkdir(parents=True, exist_ok=True)
    if not setup.exists():
        print("[SETUP] downloading trusted setup...")
        urllib.request.urlretrieve(
            "https://raw.githubusercontent.com/ethereum/c-kzg-4844/main/src/trusted_setup.txt",
            setup,
        )
    try:
        return ckzg.load_trusted_setup(str(setup), 0), setup
    except TypeError:
        return ckzg.load_trusted_setup(str(setup)), setup


def _build_blob(payload_bytes: bytes) -> bytes:
    blob = bytearray(131072)
    for i, off in enumerate(range(0, len(payload_bytes), 31)):
        chunk = payload_bytes[off : off + 31]
        p = i * 32
        blob[p] = 0
        blob[p + 1 : p + 1 + len(chunk)] = chunk
    return bytes(blob)


def _main():
    priv = _read_private_key()
    hashes = _resolve_aem_hashes()

    acct = Account.from_key(priv)
    wallet = acct.address
    ts_now = int(time.time())
    signer_identity = os.environ.get("ETHICBIT_AEM_SIGNER_IDENTITY", "UNSPECIFIED")

    try:
        git_sha = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=str(ROOT)).decode().strip()
    except Exception:
        git_sha = "unknown"

    payload_obj = {
        "v": 1,
        "schema": "ETHICBIT_AEM_MAINNET_PAYLOAD_V1",
        "anchor_for": "AEM_V1_1_CANONICAL_AND_THESIS",
        "canonical_sha256": hashes["canonical_sha256"],
        "thesis_sha256": hashes["thesis_sha256"],
        "system_state_sha256": hashes["system_state_sha256"],
        "freeze_pdf_sha256": hashes["freeze_pdf_sha256"],
        "repo_commit_sha": git_sha,
        "signer_address": wallet,
        "signer_identity": signer_identity,
        "ts_unix": ts_now,
        "network_target": "ethereum-mainnet",
        "purpose": "ETHICBIT AEM V1.1 mainnet anchor",
    }
    payload_bytes = json.dumps(payload_obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    print(f"[PAYLOAD] {len(payload_bytes)}B canonical={hashes['canonical_sha256'][:16]}... thesis={hashes['thesis_sha256'][:16]}...")

    ts, setup_path = _load_kzg_setup()
    print(f"[SETUP] loaded from {setup_path}")

    blob_b = _build_blob(payload_bytes)
    commitment = ckzg.blob_to_kzg_commitment(blob_b, ts)
    proof = ckzg.compute_blob_kzg_proof(blob_b, commitment, ts)
    if not ckzg.verify_blob_kzg_proof(blob_b, commitment, proof, ts):
        print("FAIL: KZG self-verify")
        sys.exit(2)
    vh = bytes([0x01]) + hashlib.sha256(commitment).digest()[1:]
    print(f"[KZG] versioned_hash=0x{vh.hex()}")

    nonce_hex, _ = rpc_call("eth_getTransactionCount", [wallet, "latest"])
    nonce = int(nonce_hex, 16)
    try:
        fh, _ = rpc_call("eth_feeHistory", [hex(4), "latest", [50]])
        base = int(fh["baseFeePerGas"][-1], 16)
    except Exception:
        base = 35 * 10**9
    max_pri = 2 * 10**9
    max_fee = base * 2 + max_pri
    try:
        bbf, _ = rpc_call("eth_blobBaseFee", [])
        blob_base = int(bbf, 16) if isinstance(bbf, str) else 1
    except Exception:
        blob_base = 1
    max_blob_fee = max(blob_base * 4, 2 * 10**9)
    print(f"[TX] nonce={nonce} maxFee={max_fee/1e9:.2f}gwei maxBlob={max_blob_fee/1e9:.2f}gwei")

    tx = {
        "type": 3,
        "chainId": 1,
        "nonce": nonce,
        "to": wallet,
        "value": 0,
        "data": b"",
        "gas": 25000,
        "maxPriorityFeePerGas": max_pri,
        "maxFeePerGas": max_fee,
        "maxFeePerBlobGas": max_blob_fee,
        "blobVersionedHashes": [vh],
    }

    signed = Account.sign_transaction(tx, private_key=priv, blobs=[blob_b])
    raw = getattr(signed, "raw_transaction", None) or signed.rawTransaction
    raw_hex = raw.hex() if isinstance(raw, bytes) else raw
    if not raw_hex.startswith("0x"):
        raw_hex = "0x" + raw_hex

    if DRY:
        estimated_cost_eth = (max_fee * 25000 + max_blob_fee * 131072) / 10**18
        print("\n=== DRY_RUN: no broadcast ===")
        print(f"  payload_size_bytes : {len(payload_bytes)}")
        print(f"  blob_size_bytes    : {len(blob_b)}")
        print(f"  commitment_size    : {len(commitment)}")
        print(f"  proof_size         : {len(proof)}")
        print(f"  versioned_hash     : 0x{vh.hex()}")
        print(f"  raw_tx_size_bytes  : {len(raw)}")
        print(f"  estimated_cost_eth : {estimated_cost_eth:.6f}")
        print("\nDry-run PASS. Re-run with DRY_RUN unset to broadcast.")
        return

    tx_hash, used_rpc = rpc_call("eth_sendRawTransaction", [raw_hex])
    print(f"[TX] broadcast: {tx_hash}")
    print(f"[TX] via      : {used_rpc}")

    print("[WAIT] waiting for receipt...")
    receipt = None
    for i in range(72):
        time.sleep(5)
        try:
            rr, _ = rpc_call("eth_getTransactionReceipt", [tx_hash])
            if rr:
                receipt = rr
                break
        except Exception:
            pass
        if i % 6 == 0:
            print(f"  ...{i+1}/72")

    if not receipt:
        print("FAIL: no receipt after ~6 minutes")
        sys.exit(2)

    status = int(receipt["status"], 16)
    if status != 1:
        print(f"FAIL: tx reverted at block={int(receipt['blockNumber'],16)}")
        sys.exit(2)

    block_n = int(receipt["blockNumber"], 16)
    tx_data, _ = rpc_call("eth_getTransactionByHash", [tx_hash])

    report = {
        "schema_id": "ETHICBIT_AEM_MAINNET_ANCHOR_REPORT_V1",
        "status": "ONCHAIN_BLOB_ANCHOR_VERIFIED",
        "network": "ethereum-mainnet",
        "chain_id": 1,
        "rpc_endpoint": used_rpc,
        "tx_hash": tx_hash,
        "tx_type": tx_data.get("type", "0x3"),
        "block_number": block_n,
        "from_address": tx_data.get("from", wallet),
        "to_address": tx_data.get("to", wallet),
        "blob_versioned_hashes": ["0x" + vh.hex()],
        "blob_count": 1,
        "blob_gas_used_int": int(receipt.get("blobGasUsed", "0x20000"), 16),
        "anchored_payload": payload_obj,
        "anchored_at_unix": ts_now,
    }
    report_path = ROOT / "results" / "aem_v1_1_mainnet_anchor_report.json"
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True))
    print(f"[REPORT] {report_path}")

    # Re-sign constitutional ceiling to keep custody linkage workflow consistent.
    ceiling_path = ROOT / "results" / "constitutional_evidence_ceiling.json"
    if ceiling_path.exists():
        canonical = json.dumps(
            json.loads(ceiling_path.read_text()),
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        )
        msg = encode_defunct(text=canonical)
        sm = Account.sign_message(msg, private_key=priv)
        mh = getattr(sm, "message_hash", None) or sm.messageHash
        sg = sm.signature
        mh_hex = mh.hex() if hasattr(mh, "hex") else str(mh)
        sg_hex = sg.hex() if hasattr(sg, "hex") else str(sg)
        if not mh_hex.startswith("0x"):
            mh_hex = "0x" + mh_hex
        if not sg_hex.startswith("0x"):
            sg_hex = "0x" + sg_hex
        sig_obj = {
            "schema_id": "ETHICBIT_CEILING_SIGNATURE_V1",
            "scheme": "EIP-191_personal_sign",
            "canonicalization": "json_sort_keys_no_whitespace_utf8",
            "ceiling_filename": "constitutional_evidence_ceiling.json",
            "message_hash": mh_hex,
            "signature": sg_hex,
            "signer_address": acct.address,
            "signed_at_unix": int(time.time()),
        }
        (ROOT / "results" / "constitutional_evidence_ceiling.sig").write_text(
            json.dumps(sig_obj, indent=2, sort_keys=True)
        )
        print("[SIG] constitutional_evidence_ceiling.sig refreshed")

    print("\n" + "=" * 64)
    print("AEM V1.1 MAINNET ANCHOR COMPLETE")
    print("=" * 64)
    print(f"  tx_hash     : {tx_hash}")
    print(f"  block       : {block_n}")
    print(f"  canonical   : {hashes['canonical_sha256']}")
    print(f"  thesis      : {hashes['thesis_sha256']}")
    print(f"  system_sha  : {hashes['system_state_sha256']}")
    if hashes["freeze_pdf_sha256"]:
        print(f"  freeze_pdf  : {hashes['freeze_pdf_sha256']}")


if __name__ == "__main__":
    _main()
