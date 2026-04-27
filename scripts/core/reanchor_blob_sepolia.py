#!/usr/bin/env python3
"""Re-anchor periódico: emite nueva TX EIP-4844 type-3 con blob conteniendo
hash del estado actual del repo (ceiling_sha256 + git_commit_sha + ts).
Tras confirmación, actualiza kzg_blob_anchor_report.json y re-firma ceiling.sig.

Vars:
  DRY_RUN=1   -> hace todo EXCEPTO enviar la TX (validación cripto sin gastar gas)
"""
import os, sys, json, time, hashlib, subprocess, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DRY = os.environ.get("DRY_RUN") == "1"

# 1) priv key
priv = os.environ.get("ETHICBIT_PRIVATE_KEY")
if not priv:
    for ln in (ROOT/".env").read_text().splitlines():
        s = ln.strip()
        if s.startswith("ETHICBIT_PRIVATE_KEY="):
            priv = s.split("=",1)[1].strip().strip('"').strip("'"); break
if not priv: print("FAIL: no ETHICBIT_PRIVATE_KEY"); sys.exit(2)
if not priv.startswith("0x"): priv = "0x" + priv

# 2) RPC fallback
RPCS = ["https://sepolia.drpc.org","https://1rpc.io/sepolia",
        "https://gateway.tenderly.co/public/sepolia",
        "https://ethereum-sepolia-rpc.publicnode.com"]
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
    raise RuntimeError(f"all RPCs failed for {method}: {last}")

# 3) imports cripto
from eth_account import Account
from eth_account.messages import encode_defunct
import ckzg

# 4) trusted setup
SETUP_PATH = ROOT/"scripts"/"core"/"kzg_setup"/"trusted_setup.txt"
SETUP_PATH.parent.mkdir(parents=True, exist_ok=True)
if not SETUP_PATH.exists():
    print("[SETUP] descargando trusted setup oficial...")
    url = "https://raw.githubusercontent.com/ethereum/c-kzg-4844/main/src/trusted_setup.txt"
    urllib.request.urlretrieve(url, SETUP_PATH)
    print(f"[SETUP] guardado {SETUP_PATH.stat().st_size} bytes")
try:
    ts = ckzg.load_trusted_setup(str(SETUP_PATH), 0)
except TypeError:
    ts = ckzg.load_trusted_setup(str(SETUP_PATH))
print("[SETUP] cargado")

# 5) construir payload
ceiling = json.loads((ROOT/"results"/"constitutional_evidence_ceiling.json").read_text())
canonical = json.dumps(ceiling, sort_keys=True, separators=(",",":"), ensure_ascii=False)
ceiling_sha = hashlib.sha256(canonical.encode()).hexdigest()
try:
    git_sha = subprocess.check_output(["git","rev-parse","HEAD"], cwd=str(ROOT)).decode().strip()
except Exception:
    git_sha = "unknown"
acct = Account.from_key(priv)
wallet = acct.address
ts_now = int(time.time())
payload = json.dumps({
    "v":1,"schema":"ETHICBIT_BLOB_PAYLOAD_V1",
    "anchor_for":"constitutional_evidence_ceiling.json",
    "ceiling_sha256":ceiling_sha,"git_commit_sha":git_sha,
    "wallet":wallet,"ts_unix":ts_now,
    "purpose":"ETHICBIT L5 periodic re-anchor"
}, sort_keys=True, separators=(",",":")).encode()
print(f"[PAYLOAD] {len(payload)}B  ceiling_sha={ceiling_sha[:16]}...  git={git_sha[:8]}")

# 6) construir blob: 4096 field elements de 32B, primer byte=0
BLOB_SIZE, FE = 131072, 32
blob = bytearray(BLOB_SIZE)
for i, off in enumerate(range(0, len(payload), 31)):
    chunk = payload[off:off+31]
    p = i*FE
    blob[p] = 0
    blob[p+1:p+1+len(chunk)] = chunk
blob_b = bytes(blob)
print(f"[BLOB] {len(blob_b)}B (payload {len(payload)}B + zero-pad)")

# 7) KZG
commitment = ckzg.blob_to_kzg_commitment(blob_b, ts)
proof = ckzg.compute_blob_kzg_proof(blob_b, commitment, ts)
if not ckzg.verify_blob_kzg_proof(blob_b, commitment, proof, ts):
    print("FAIL: KZG self-verify"); sys.exit(2)
vh = bytes([0x01]) + hashlib.sha256(commitment).digest()[1:]
print(f"[KZG] commit={len(commitment)}B proof={len(proof)}B")
print(f"[KZG] versioned_hash=0x{vh.hex()}")

# 8) construir tx
nonce_hex,_ = rpc_call("eth_getTransactionCount", [wallet, "latest"])
nonce = int(nonce_hex, 16)
try:
    fh,_ = rpc_call("eth_feeHistory", [hex(4), "latest", [50]])
    base = int(fh["baseFeePerGas"][-1], 16)
except Exception:
    base = 5*10**9
max_pri = 2*10**9
max_fee = base*3 + max_pri
try:
    bbf,_ = rpc_call("eth_blobBaseFee", [])
    blob_base = int(bbf, 16) if isinstance(bbf,str) else 1
except Exception:
    blob_base = 1
max_blob_fee = max(blob_base*5, 10**9)
print(f"[TX] nonce={nonce} maxFee={max_fee/1e9:.2f}gw maxBlob={max_blob_fee/1e9:.2f}gw")

tx = {'type':3,'chainId':11155111,'nonce':nonce,'to':wallet,'value':0,'data':b'',
      'gas':25000,'maxPriorityFeePerGas':max_pri,'maxFeePerGas':max_fee,
      'maxFeePerBlobGas':max_blob_fee,'blobVersionedHashes':[vh]}

signed = Account.sign_transaction(tx, private_key=priv, blobs=[blob_b])
raw = getattr(signed, 'raw_transaction', None) or signed.rawTransaction
raw_hex = raw.hex() if isinstance(raw, bytes) else raw
if not raw_hex.startswith("0x"): raw_hex = "0x" + raw_hex
print(f"[TX] firmada raw={len(raw)}B")

if DRY:
    print("\n=== DRY_RUN: no se envía la TX ===")
    print(f"  payload_size_bytes : {len(payload)}")
    print(f"  blob_size_bytes    : {len(blob_b)}")
    print(f"  commitment_size    : {len(commitment)}")
    print(f"  proof_size         : {len(proof)}")
    print(f"  versioned_hash     : 0x{vh.hex()}")
    print(f"  raw_tx_size_bytes  : {len(raw)}")
    print(f"  estimated_cost_eth : {(max_fee*25000 + max_blob_fee*131072)/10**18:.6f}")
    print("\n  All cryptographic primitives validated.")
    print("  Re-run without DRY_RUN=1 to actually broadcast.")
    sys.exit(0)

# 9) enviar
tx_hash, used_rpc = rpc_call("eth_sendRawTransaction", [raw_hex])
print(f"[TX] enviada: {tx_hash}")
print(f"[TX] via   : {used_rpc}")

# 10) esperar
print("[WAIT] esperando confirmación...")
receipt = None
for i in range(60):
    time.sleep(5)
    try:
        r,_ = rpc_call("eth_getTransactionReceipt", [tx_hash])
        if r:
            receipt = r; break
    except Exception: pass
    if i%6==0: print(f"  ...{i+1}/60")
if not receipt:
    print("FAIL: no confirmada en 5min"); sys.exit(2)
status = int(receipt["status"], 16)
if status != 1:
    print(f"FAIL: TX reverted block={int(receipt['blockNumber'],16)}"); sys.exit(2)
block_n = int(receipt["blockNumber"], 16)
print(f"[CONFIRMED] block={block_n} status=success")

# 11) detalles tx
tx_data,_ = rpc_call("eth_getTransactionByHash", [tx_hash])

# 12) actualizar report
report = {
    "schema_id":"ETHICBIT_KZG_BLOB_ANCHOR_V1",
    "status":"ONCHAIN_BLOB_ANCHOR_VERIFIED",
    "verification_method":"rpc_eth_sendRawTransaction_with_eip4844_blob_sidecar",
    "rpc_endpoint":used_rpc,"chain_id":11155111,"tx_hash":tx_hash,
    "tx_type":tx_data.get("type","0x3"),"block_number":block_n,
    "from_address":tx_data.get("from",wallet),"to_address":tx_data.get("to",wallet),
    "blob_versioned_hashes":["0x"+vh.hex()],"blob_count":1,
    "blob_gas_used_int":int(receipt.get("blobGasUsed","0x20000"),16),
    "evidence_strength":"VERIFIED_BY_INDEPENDENT_PUBLIC_RPC",
    "anchored_payload":{"ceiling_sha256":ceiling_sha,"git_commit_sha":git_sha,"ts_unix":ts_now},
    "anchored_at_unix":ts_now
}
(ROOT/"results"/"kzg_blob_anchor_report.json").write_text(json.dumps(report, indent=2, sort_keys=True))
print(f"[REPORT] kzg_blob_anchor_report.json actualizado")

# 13) re-firmar ceiling
msg = encode_defunct(text=canonical)
sm = Account.sign_message(msg, private_key=priv)
mh = (getattr(sm,"message_hash",None) or sm.messageHash)
sg = sm.signature
mh_hex = mh.hex() if hasattr(mh,"hex") else str(mh)
sg_hex = sg.hex() if hasattr(sg,"hex") else str(sg)
if not mh_hex.startswith("0x"): mh_hex="0x"+mh_hex
if not sg_hex.startswith("0x"): sg_hex="0x"+sg_hex
sig_obj = {"schema_id":"ETHICBIT_CEILING_SIGNATURE_V1",
    "scheme":"EIP-191_personal_sign",
    "canonicalization":"json_sort_keys_no_whitespace_utf8",
    "ceiling_filename":"constitutional_evidence_ceiling.json",
    "message_hash":mh_hex,"signature":sg_hex,
    "signer_address":acct.address,"signed_at_unix":int(time.time())}
(ROOT/"results"/"constitutional_evidence_ceiling.sig").write_text(
    json.dumps(sig_obj, indent=2, sort_keys=True))
print("[SIG] ceiling.sig re-firmado")

print("\n"+"="*64)
print("RE-ANCHOR COMPLETO")
print("="*64)
print(f"  tx_hash       : {tx_hash}")
print(f"  block         : {block_n}")
print(f"  versioned_hash: 0x{vh.hex()}")
print(f"  ceiling_sha   : {ceiling_sha}")
print(f"  git_commit    : {git_sha}")
