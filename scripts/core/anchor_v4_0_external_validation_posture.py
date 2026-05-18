#!/usr/bin/env python3
"""
Anchor v4.0 External Validation posture on Ethereum mainnet — EIP-4844 type-3 KZG blob TX.

Re-anchor after all remediation blocks (A, B1-B5, C, D, E) are complete.

Anchors:
  - assurance/slsa/subject-index.json           (4/4 BOUND)
  - assurance/sbom/aem_v1_1_sbom.cyclonedx.json (654 components, KMS-signed)
  - assurance/sbom/aem_v1_1_sbom.cyclonedx.sig.json (detached sidecar)
  - assurance/in-toto/attestation-index.json    (6/6 KMS_SIGNED)
  - assurance/threat-model/threat-model.json    (21 threats, STRIDE/LINDDUN/ATLAS)
  - assurance/anchor/anchor-policy.json         (programmatic anchor policy)
  - assurance/v4_0/V4_0_EXTERNAL_VALIDATION_INITIATION_RECORD_V2.json
  - docs/assurance/SIGNING_KEY_MIGRATION_RECORD.md (Block B1)

Outputs:
  assurance/v4_0/V4_0_EV_POSTURE_MAINNET_ANCHOR_RECEIPT.json
  assurance/v4_0/V4_0_EV_POSTURE_SEPOLIA_ANCHOR_RECEIPT.json (if --sepolia)

DRY_RUN=1  -> validates payload + KZG, prints versioned_hash, never broadcasts.
BROADCAST=1 -> required to actually broadcast.
"""
from __future__ import annotations

import datetime
import hashlib
import json
import os
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DRY = os.environ.get("DRY_RUN") == "1"
NETWORK = os.environ.get("ANCHOR_NETWORK", "mainnet")  # "mainnet" or "sepolia"

MAINNET_RPCS = [
    "https://ethereum-rpc.publicnode.com",
    "https://eth.drpc.org",
    "https://1rpc.io/eth",
    "https://rpc.ankr.com/eth",
]
SEPOLIA_RPCS = [
    "https://ethereum-sepolia-rpc.publicnode.com",
    "https://sepolia.drpc.org",
    "https://rpc.ankr.com/eth_sepolia",
]

ANCHOR_ARTIFACTS = {
    "subject_index":        "assurance/slsa/subject-index.json",
    "sbom_cyclonedx":       "assurance/sbom/aem_v1_1_sbom.cyclonedx.json",
    "sbom_sig":             "assurance/sbom/aem_v1_1_sbom.cyclonedx.sig.json",
    "intoto_index":         "assurance/in-toto/attestation-index.json",
    "threat_model":         "assurance/threat-model/threat-model.json",
    "anchor_policy":        "assurance/anchor/anchor-policy.json",
    "initiation_record_v2": "assurance/v4_0/V4_0_EXTERNAL_VALIDATION_INITIATION_RECORD_V2.json",
    "signing_migration_b1": "docs/assurance/SIGNING_KEY_MIGRATION_RECORD.md",
}

KZG_SETUP = ROOT / "scripts/core/kzg_setup/trusted_setup.txt"
MAINNET_RECEIPT_OUT = ROOT / "assurance/v4_0/V4_0_EV_POSTURE_MAINNET_ANCHOR_RECEIPT.json"
SEPOLIA_RECEIPT_OUT = ROOT / "assurance/v4_0/V4_0_EV_POSTURE_SEPOLIA_ANCHOR_RECEIPT.json"

PREVIOUS_MAINNET_ANCHOR = {
    "block": 25095358,
    "tx": "0xd5fe44459f15e1cb3230f841f039d35d73da84564963fb4b32dcb9000da2cb41",
    "scope": "v4.0 controlled evidence — 2026-05-14",
}


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def now_utc() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def rpc_call(method, params, timeout=20):
    rpcs = SEPOLIA_RPCS if NETWORK == "sepolia" else MAINNET_RPCS
    last = None
    for rpc in rpcs:
        try:
            body = json.dumps({"jsonrpc": "2.0", "id": 1, "method": method, "params": params}).encode()
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
        print("FAIL: ETHICBIT_PRIVATE_KEY not set")
        sys.exit(2)
    return priv if priv.startswith("0x") else "0x" + priv


def build_blob(payload_bytes: bytes) -> bytes:
    blob = bytearray(131072)
    for i, off in enumerate(range(0, len(payload_bytes), 31)):
        chunk = payload_bytes[off:off + 31]
        p = i * 32
        blob[p] = 0
        blob[p + 1:p + 1 + len(chunk)] = chunk
    return bytes(blob)


def build_payload() -> dict:
    artifact_hashes = {}
    for name, rel in ANCHOR_ARTIFACTS.items():
        p = ROOT / rel
        if p.exists():
            artifact_hashes[name] = sha256_file(p)
        else:
            print(f"  WARN: artifact missing — {rel}")
            artifact_hashes[name] = "MISSING"

    git_sha = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT).decode().strip()

    return {
        "schema": "ETHICBIT_AEM_V4_0_EV_POSTURE_ANCHOR_V1",
        "anchor_scope": (
            "v4.0 External Validation posture re-anchor — all remediation blocks complete "
            "(A, B1-B5, C, D, E) — 2026-05-18"
        ),
        "constitutional_dependency": "EthicBit/CEMU/v3.7.0+",
        "release_class": "EXTERNAL_VALIDATION",
        "remediation_blocks_completed": ["A", "B1", "B2", "B3", "B4", "B5", "C", "D", "E"],
        "criteria_controlled_pass": 5,
        "criteria_pending_external": 3,
        "criteria_pending_external_list": [1, 2, 8],
        "signing_posture": "PRODUCTION_HSM_READY",
        "intoto_chain_status": "KMS_SIGNED_PENDING_EXTERNAL_WITNESS",
        "intoto_steps_signed": 6,
        "sbom_components": 654,
        "sbom_kms_signed": True,
        "slsa_builder_workflow": "ACTIVE",
        "claim_boundary_block_rate": 100.0,
        "hypothesis_tests_passed": 8,
        "test_suite_passed": 15,
        "previous_mainnet_anchor": PREVIOUS_MAINNET_ANCHOR,
        "artifact_hashes": artifact_hashes,
        "git_commit_sha": git_sha,
        "ts_unix": int(time.time()),
        "non_claim": (
            "Anchor — timestamped integrity reference for v4.0 External Validation posture "
            "after all remediation blocks complete. Does not claim external validation pass, "
            "third-party reproduced, production-ready, or human attestation complete. "
            "Criteria 1, 2, 8 remain PENDING_EXTERNAL."
        ),
    }


def main() -> None:
    sep = "=" * 64
    print(sep)
    print(f"EthicBit / AEM-EVOLVE v4.0 EV Posture Anchor — {NETWORK.upper()}")
    print(sep)
    if DRY:
        print("DRY_RUN=1 — payload + KZG only, no broadcast")
    print()

    # ── Build payload ────────────────────────────────────────────────
    payload_dict = build_payload()
    payload_bytes = json.dumps(payload_dict, sort_keys=True, separators=(",", ":")).encode()
    payload_sha256 = hashlib.sha256(payload_bytes).hexdigest()
    payload_dict["payload_sha256"] = payload_sha256

    print(f"Payload built    {len(payload_bytes)} bytes")
    print(f"Payload SHA256:  {payload_sha256}")
    print(f"git_commit:      {payload_dict['git_commit_sha'][:16]}...")
    print()
    print("Artifact hashes:")
    for k, v in payload_dict["artifact_hashes"].items():
        print(f"  {k:<30s}  {v[:16]}...")
    print()

    # ── KZG blob ─────────────────────────────────────────────────────
    try:
        import ckzg
    except ImportError:
        print("FAIL: ckzg not installed — pip install ckzg")
        sys.exit(2)

    ts = ckzg.load_trusted_setup(str(KZG_SETUP), 0)
    blob_b = build_blob(payload_bytes)
    commit = ckzg.blob_to_kzg_commitment(blob_b, ts)
    proof = ckzg.compute_blob_kzg_proof(blob_b, commit, ts)
    if not ckzg.verify_blob_kzg_proof(blob_b, commit, proof, ts):
        print("FAIL: KZG proof verification failed")
        sys.exit(2)

    vh = b"\x01" + hashlib.sha256(commit).digest()[1:]
    print(f"KZG commitment:  {commit.hex()[:16]}...")
    print(f"Versioned hash:  0x{vh.hex()}")
    print()

    if DRY:
        print("DRY_RUN complete — payload and KZG verified. Set BROADCAST=1 to broadcast.")
        # Write a dry-run preparation record
        receipt_out = MAINNET_RECEIPT_OUT if NETWORK == "mainnet" else SEPOLIA_RECEIPT_OUT
        dry_record = {
            "schema_id": "ETHICBIT_AEM_V4_0_EV_POSTURE_ANCHOR_V1",
            "status": "PENDING_BROADCAST",
            "network": f"ethereum-{NETWORK}",
            "prepared_at": now_utc(),
            "payload_sha256": payload_sha256,
            "blob_versioned_hash_dry": f"0x{vh.hex()}",
            "payload": payload_dict,
            "non_claim": payload_dict["non_claim"],
        }
        receipt_out.parent.mkdir(parents=True, exist_ok=True)
        receipt_out.write_text(json.dumps(dry_record, indent=2))
        print(f"Dry-run record → {receipt_out.relative_to(ROOT)}")
        return

    if os.environ.get("BROADCAST") != "1":
        print("Set BROADCAST=1 to broadcast (DRY_RUN=1 skips broadcast).")
        sys.exit(0)

    # ── Broadcast ────────────────────────────────────────────────────
    priv = load_priv_key()
    try:
        from eth_account import Account
        from eth_account.typed_transactions import BlobTransaction
        from web3 import Web3
    except ImportError:
        print("FAIL: eth_account / web3 not installed")
        sys.exit(2)

    wallet = Account.from_key(priv).address
    print(f"Wallet: {wallet}")

    chain_id = 11155111 if NETWORK == "sepolia" else 1
    nonce_hex, used_rpc = rpc_call("eth_getTransactionCount", [wallet, "latest"])
    nonce = int(nonce_hex, 16)
    print(f"RPC: {used_rpc}  nonce={nonce}")

    try:
        fh, _ = rpc_call("eth_feeHistory", ["0x5", "latest", []])
        base = int(fh["baseFeePerGas"][-1], 16)
    except Exception:
        base = 5 * 10**9
    max_priority = 2 * 10**9
    max_fee = base * 2 + max_priority

    try:
        bbf, _ = rpc_call("eth_blobBaseFee", [])
        max_blob_fee = max(int(bbf, 16) * 2, 10**9)
    except Exception:
        max_blob_fee = 10**9

    tx = {
        "type": 3,
        "chainId": chain_id,
        "nonce": nonce,
        "to": wallet,
        "value": 0,
        "data": b"",
        "gas": 21000,
        "maxFeePerGas": max_fee,
        "maxPriorityFeePerGas": max_priority,
        "maxFeePerBlobGas": max_blob_fee,
        "blobVersionedHashes": [vh],
    }

    signed = Account.sign_transaction(tx, private_key=priv, blobs=[blob_b])
    ts_start = int(time.time())
    raw = getattr(signed, "raw_transaction", None) or signed.rawTransaction
    raw_hex = raw.hex() if isinstance(raw, bytes) else raw
    if not raw_hex.startswith("0x"):
        raw_hex = "0x" + raw_hex
    tx_hash_result, _ = rpc_call("eth_sendRawTransaction", [raw_hex])
    tx_hash = tx_hash_result
    tx_hash = raw_hex
    print(f"TX submitted: {tx_hash}")
    print(f"Versioned hash: 0x{vh.hex()}")

    print("Waiting for receipt", end="", flush=True)
    receipt = None
    for _ in range(60):
        time.sleep(4)
        print(".", end="", flush=True)
        try:
            result, _ = rpc_call("eth_getTransactionReceipt", [tx_hash])
            if result:
                receipt = result
                break
        except Exception:
            pass
    print()

    if not receipt:
        print("WARN: Receipt not confirmed within 4 minutes")
        receipt = {}

    block_num = int(receipt.get("blockNumber", "0x0"), 16) if receipt else 0
    receipt_out = MAINNET_RECEIPT_OUT if NETWORK == "mainnet" else SEPOLIA_RECEIPT_OUT
    receipt_doc = {
        "schema_id": "ETHICBIT_AEM_V4_0_EV_POSTURE_ANCHOR_V1",
        "status": "ONCHAIN_BLOB_ANCHOR_VERIFIED" if receipt else "TX_SUBMITTED_RECEIPT_PENDING",
        "network": f"ethereum-{NETWORK}",
        "chain_id": chain_id,
        "block_number": block_num,
        "tx_hash": tx_hash,
        "block_explorer_url": (
            f"https://{'sepolia.' if NETWORK == 'sepolia' else ''}etherscan.io/tx/{tx_hash}"
        ),
        "from_address": wallet,
        "to_address": wallet,
        "blob_versioned_hashes": [f"0x{vh.hex()}"],
        "timestamp_utc": now_utc(),
        "anchored_at_unix": ts_start,
        "payload": payload_dict,
        "non_claim": payload_dict["non_claim"],
    }
    receipt_out.parent.mkdir(parents=True, exist_ok=True)
    receipt_out.write_text(json.dumps(receipt_doc, indent=2))
    print(f"Receipt → {receipt_out.relative_to(ROOT)}")

    if NETWORK == "mainnet":
        print(f"Explorer: https://etherscan.io/tx/{tx_hash}")
    else:
        print(f"Explorer: https://sepolia.etherscan.io/tx/{tx_hash}")


if __name__ == "__main__":
    main()
