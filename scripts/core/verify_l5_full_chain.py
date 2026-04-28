#!/usr/bin/env python3
"""verify_l5_full_chain.py — verificador integral de L5.
Exige que pasen los tres stages:
  STAGE 1: verify_l5_canonical_state.py  (runtime + ceiling + blob anchor JSON)
  STAGE 2: verify_ceiling_signature.py   (cadena de custodia EIP-191 <-> EIP-4844)
  STAGE 3: verify_l5_onchain.py          (cross-verify anchor against public RPCs)
Exit=0 sólo si los tres pasan."""
import subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
v1 = ROOT / "scripts" / "core" / "verify_l5_canonical_state.py"
v2 = ROOT / "scripts" / "core" / "verify_ceiling_signature.py"
v3 = ROOT / "scripts" / "core" / "verify_l5_onchain.py"

for p in (v1, v2, v3):
    if not p.exists():
        print(f"FAIL: falta {p}"); sys.exit(2)

def stage(num, label, script):
    print("=" * 64)
    print(f"STAGE {num}: {label}")
    print("=" * 64)
    r = subprocess.run([sys.executable, str(script)])
    print(f"\n[STAGE{num} exit={r.returncode}]\n")
    return r.returncode

rc1 = stage(1, "estado canónico L5 (runtime + ceiling + blob anchor JSON)", v1)
rc2 = stage(2, "cadena de custodia criptográfica (ceiling.sig <-> EIP-4844)", v2)
rc3 = stage(3, "cross-verify on-chain (TX existe en RPCs públicos)", v3)

print("=" * 64)
print("RESUMEN")
print("=" * 64)
print(f"  estado_canonico  : {'PASS' if rc1 == 0 else 'FAIL'}  (rc={rc1})")
print(f"  cadena_custodia  : {'PASS' if rc2 == 0 else 'FAIL'}  (rc={rc2})")
print(f"  onchain_crossvfy : {'PASS' if rc3 == 0 else 'FAIL'}  (rc={rc3})")

if rc1 == 0 and rc2 == 0 and rc3 == 0:
    print("\nL5_FULL_CHAIN=PASS")
    print("  - blob EIP-4844 verificado on-chain por RPC público independiente")
    print("  - ceiling V2.1 con eligible_for_l5=True desde 5 fuentes")
    print("  - firma EIP-191 del ceiling recupera la misma dirección que firmó la TX")
    print("  - TX existe on-chain con propiedades coincidentes (anti-tampering)")
    sys.exit(0)
else:
    print("\nL5_FULL_CHAIN=FAIL")
    sys.exit(1)
