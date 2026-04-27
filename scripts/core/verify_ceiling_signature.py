#!/usr/bin/env python3
"""Hardening #1 verifier: cadena de custodia criptográfica.
Recupera el signer del .sig sobre el JSON canónico del ceiling y lo compara
contra from_address del blob anchor TX (EIP-4844)."""
import json, sys
from pathlib import Path
from eth_account import Account
from eth_account.messages import encode_defunct

ROOT = Path(__file__).resolve().parents[2]
ceiling_path = ROOT / "results" / "constitutional_evidence_ceiling.json"
sig_path     = ROOT / "results" / "constitutional_evidence_ceiling.sig"
anchor_path  = ROOT / "results" / "kzg_blob_anchor_report.json"

for p in (ceiling_path, sig_path, anchor_path):
    if not p.exists():
        print(f"FAIL: falta {p}"); sys.exit(2)

ceiling = json.loads(ceiling_path.read_text())
sig     = json.loads(sig_path.read_text())
anchor  = json.loads(anchor_path.read_text())

canonical = json.dumps(ceiling, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
msg = encode_defunct(text=canonical)

try:
    recovered = Account.recover_message(msg, signature=sig["signature"])
except Exception as e:
    print(f"FAIL: recovery error: {e}"); sys.exit(2)

claimed     = sig.get("signer_address", "")
anchor_from = anchor.get("from_address", "")

print(f"[VERIFY] recovered_address   = {recovered}")
print(f"[VERIFY] claimed_signer      = {claimed}")
print(f"[VERIFY] blob_anchor.from    = {anchor_from}")

if recovered.lower() != claimed.lower():
    print("FAIL: recovered != claimed signer"); sys.exit(1)
if recovered.lower() != anchor_from.lower():
    print("FAIL: signer != blob_anchor.from_address (cadena de custodia rota)"); sys.exit(1)

print("PASS: ceiling.sig recupera la misma dirección que firmó la TX EIP-4844")
print("CHAIN_OF_CUSTODY=VERIFIED")
sys.exit(0)
