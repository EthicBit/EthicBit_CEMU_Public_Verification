#!/bin/bash
echo "=== GATE DE PRE-DEPLOY: Triple Public Anchor Check ==="
cd integration/anchor_verifier
./src/anchor_verifier_production.py
if [ $? -eq 0 ]; then
  echo "✅ GATE PASS - Producción controlada autorizada"
  exit 0
else
  echo "❌ GATE FAIL - Anchor no reconciliado"
  exit 1
fi
