#!/usr/bin/env bash
set -euo pipefail

echo "========================================"
echo "AUDITORIA COMPLETA EthicBit_CEMU + SLSA L4"
echo "========================================"

echo
echo "1. Hardhat compile"
npx hardhat compile --force

echo
echo "2. Slither"
slither . --solc-remaps "@nomicfoundation= node_modules/@nomicfoundation"

echo
echo "3. Hermetic Build (SLSA L4)"
npm run build:hermetic

echo
echo "4. in-toto + SLSA L4 verification"
in-toto-verify -l assurance/in-toto/root.layout

echo
echo "5. RuntimeGuard L4 check"
python3 -m cemu.builders.runtime_guard

echo
echo "AUDITORIA SLSA L4 TERMINADA (PASS)."
