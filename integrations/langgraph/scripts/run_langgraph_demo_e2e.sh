#!/usr/bin/env bash
# EthicBit LangGraph Integration — E2E runner
# Usage: bash scripts/run_langgraph_demo_e2e.sh
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INTEGRATION_DIR="$(dirname "$SCRIPT_DIR")"

echo "========================================"
echo "EthicBit LangGraph E2E — $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo "========================================"

cd "$INTEGRATION_DIR"

echo "→ Installing dependencies..."
pip install -r requirements.txt -q

echo "→ Running demo agent (DEMO_HITL_APPROVE=true)..."
DEMO_HITL_APPROVE=true python3 demo_agent.py

echo ""
echo "→ Verifying report..."
python3 - <<'EOF'
import json, pathlib, sys
report = json.loads(pathlib.Path("results/LANGGRAPH_INTEGRATION_REPORT.json").read_text())
results = report["results"]
failed = [k for k, v in results.items() if v != "PASS"]
if failed:
    print(f"FAIL — {len(failed)} checks failed: {failed}")
    sys.exit(1)

nc = report["non_claims"]
violations = [k for k, v in nc.items() if v is True]
if violations:
    print(f"FAIL — non-claim violation: {violations}")
    sys.exit(1)

print("All checks PASS. Non-claims intact.")
EOF

echo ""
echo "========================================"
echo "RESULT: PASS"
echo "Report: integrations/langgraph/results/LANGGRAPH_INTEGRATION_REPORT.json"
echo "Audit:  integrations/langgraph/results/audit_log.json"
echo "========================================"
