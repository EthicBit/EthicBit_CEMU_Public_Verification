#!/bin/bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT_DIR"

echo "=== EthicBit / CEMU - Reconcile and Show Status ==="
echo "Repo: $ROOT_DIR"
echo "UTC: $(date -u +"%Y-%m-%dT%H:%M:%SZ")"
echo

echo "[1/4] Recalculating official operational status..."
python3 scripts/status/official_operational_status_calculator.py

echo
echo "[2/4] Rebuilding derived technical artifacts..."
bash ./scripts/run_mixed_audience_audit.sh --all

echo
echo "[3/4] Exporting final status snapshot..."
python3 - <<'PY'
import json
from pathlib import Path
src = Path("artifacts/history/swarm/official_operational_status.json")
dst = Path("results/active/final_status_snapshot.json")
dst.parent.mkdir(parents=True, exist_ok=True)
data = json.loads(src.read_text(encoding="utf-8"))
snapshot = {
    "internalClosureStatus": data.get("internalClosureStatus"),
    "liveStatus": data.get("liveStatus"),
    "externalProjectionStatus": data.get("externalProjectionStatus"),
    "officialOperationalStatus": data.get("officialOperationalStatus"),
    "reason": data.get("reason"),
    "generatedAt": data.get("generatedAt"),
}
dst.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2), encoding="utf-8")
print(dst)
PY

echo
echo "[4/4] Showing reconciled state..."
echo
echo "=== OFFICIAL ==="
grep -nE '"internalClosureStatus"|"liveStatus"|"externalProjectionStatus"|"officialOperationalStatus"|"reason"' artifacts/history/swarm/official_operational_status.json || true

echo
echo "=== GATE_REPORT ==="
grep -nE 'internalClosureStatus|externalProjectionStatus|officialReasonObserved|officialExternalProjectionStatusObserved|officialOperationalStatusObserved' results/GATE_REPORT.json || true

echo
echo "=== TECHNICAL_VERIFICATION ==="
grep -nE 'Internal Closure Status|External Projection Status|Official Operational Status|Official Reason|Official Internal Closure Status|Official External Projection Status' results/technical_verification.md || true

echo
echo "=== FINAL SNAPSHOT ==="
cat results/active/final_status_snapshot.json

echo
echo "Done."
