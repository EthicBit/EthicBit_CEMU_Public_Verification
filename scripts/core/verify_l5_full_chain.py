#!/usr/bin/env python3
"""verify_l5_full_chain.py — verificador integral de L5.
Exige que pasen ambos:
  STAGE 1: verify_l5_canonical_state.py  (runtime + ceiling + blob anchor real)
  STAGE 2: verify_ceiling_signature.py   (cadena de custodia criptográfica EIP-191 ↔ EIP-4844)
Exit=0 sólo si los dos pasan."""
import subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
v1 = ROOT / "scripts" / "core" / "verify_l5_canonical_state.py"
v2 = ROOT / "scripts" / "core" / "verify_ceiling_signature.py"

for p in (v1, v2):
    if not p.exists():
        print(f"FAIL: falta {p}"); sys.exit(2)

print("=" * 64)
print("STAGE 1: estado canónico L5 (runtime + ceiling + blob anchor)")
print("=" * 64)
r1 = subprocess.run([sys.executable, str(v1)])
print(f"\n[STAGE1 exit={r1.returncode}]")

print("\n" + "=" * 64)
print("STAGE 2: cadena de custodia criptográfica (ceiling.sig ↔ blob TX)")
print("=" * 64)
r2 = subprocess.run([sys.executable, str(v2)])
print(f"\n[STAGE2 exit={r2.returncode}]")

print("\n" + "=" * 64)
print("RESUMEN")
print("=" * 64)
print(f"  estado_canonico  : {'PASS' if r1.returncode == 0 else 'FAIL'}  (rc={r1.returncode})")
print(f"  cadena_custodia  : {'PASS' if r2.returncode == 0 else 'FAIL'}  (rc={r2.returncode})")

if r1.returncode == 0 and r2.returncode == 0:
    print("\nL5_FULL_CHAIN=PASS")
    print("  - blob EIP-4844 verificado on-chain por RPC público independiente")
    print("  - ceiling V2.1 con eligible_for_l5=True desde 5 fuentes")
    print("  - firma EIP-191 del ceiling recupera la misma dirección que firmó la TX")
    sys.exit(0)
else:
    print("\nL5_FULL_CHAIN=FAIL")
    sys.exit(1)
