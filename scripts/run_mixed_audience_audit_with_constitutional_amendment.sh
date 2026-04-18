#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd -- "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

cd "$ROOT_DIR"

./scripts/run_mixed_audience_audit.sh --all
./scripts/status/write_constitutional_amendment_snapshot.py
./scripts/status/apply_constitutional_amendment_to_results.py

echo
echo "=== CONSTITUTIONAL AMENDMENT INTEGRATION COMPLETE ==="
echo "Snapshot: results/constitutional_amendment_snapshot.json"
echo "Updated: results/constitutional_controls_report.json"
echo "Updated: results/technical_verification.md"
