#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

if [ -f ".venv/bin/activate" ]; then
  # shellcheck disable=SC1091
  source .venv/bin/activate
fi

echo "=== AEM V1.1 REPRODUCIBILITY EXTENSION E2E ==="
echo "repo=$(pwd)"
echo "commit=$(git rev-parse --short HEAD)"

bash scripts/reproducibility/build_from_clean_environment.sh

echo
echo "=== SUMMARY ==="
python3 - <<'PY'
import json
from pathlib import Path

comparison = json.loads(Path("assurance/reproducibility/comparison_report.json").read_text())
receipt = json.loads(Path("receipts/AEM_V1_1_REPRODUCIBILITY_EXTENSION_RECEIPT.json").read_text())
mainnet_receipt_path = Path("receipts/AEM_V1_1_REPRODUCIBILITY_EXTENSION_MAINNET_ANCHOR_RECEIPT.json")
mainnet_receipt = {}
if mainnet_receipt_path.exists():
    mainnet_receipt = json.loads(mainnet_receipt_path.read_text())

print("comparison.status =", comparison.get("status"))
summary = comparison.get("summary", {})
print("subjects.total    =", summary.get("total"))
print("subjects.matched  =", summary.get("matched"))
print("subjects.mismatch =", summary.get("mismatched"))
print("claim.current     =", receipt.get("current_closure"))
print("claim.target      =", receipt.get("target_closure"))
print("anchor.status     =", mainnet_receipt.get("status") or receipt.get("anchor_status"))
if mainnet_receipt:
    print("anchor.tx         =", mainnet_receipt.get("tx_hash"))
    print("anchor.block      =", mainnet_receipt.get("block_number"))
PY
