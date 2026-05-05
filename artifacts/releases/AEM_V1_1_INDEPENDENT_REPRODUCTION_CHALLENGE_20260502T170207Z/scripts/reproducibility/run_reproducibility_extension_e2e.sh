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

print("comparison.status =", comparison.get("status"))
summary = comparison.get("summary", {})
print("subjects.total    =", summary.get("total"))
print("subjects.matched  =", summary.get("matched"))
print("subjects.mismatch =", summary.get("mismatched"))
print("claim.current     =", receipt.get("current_closure"))
print("claim.target      =", receipt.get("target_closure"))
print("anchor.status     =", receipt.get("anchor_status"))
PY

