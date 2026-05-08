#!/usr/bin/env bash
# Phase 2 — AEM-EVOLVE Adversarial Test Suite Runner
# Runs all adversarial test categories and aggregates results.
#
# Usage:
#   bash run_all_adversarial_tests.sh [--skip-live]
#
# --skip-live  Skip tests that require the API server (curl-based tests).
#              Tampering detection tests run regardless (no server needed).
#
# Exit codes:
#   0  ALL_PASS
#   1  FAILURES_DETECTED

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKIP_LIVE=false
for arg in "$@"; do
  [[ "$arg" == "--skip-live" ]] && SKIP_LIVE=true
done

TOTAL_PASS=0
TOTAL_FAIL=0
SKIPPED=0

run_bash_test() {
  local file="$1"
  if $SKIP_LIVE; then
    echo "  SKIPPED  [$(basename "$file")] (--skip-live)"
    SKIPPED=$((SKIPPED+1))
    return
  fi
  # Check server reachable
  if ! curl -s -o /dev/null -w "%{http_code}" "http://127.0.0.1:8000/docs" 2>/dev/null | grep -q "200"; then
    echo "  SKIPPED  [$(basename "$file")] (server not reachable on :8000)"
    SKIPPED=$((SKIPPED+1))
    return
  fi
  output=$(bash "$file" 2>&1)
  echo "$output"
  pass=$(echo "$output" | grep -oP '(?<=_PASS=)\d+' | tail -1 || echo 0)
  fail=$(echo "$output" | grep -oP '(?<=_FAIL=)\d+' | tail -1 || echo 0)
  TOTAL_PASS=$((TOTAL_PASS + pass))
  TOTAL_FAIL=$((TOTAL_FAIL + fail))
}

run_python_test() {
  local file="$1"
  output=$(python3 "$file" 2>&1)
  echo "$output"
  pass=$(echo "$output" | grep -oP '(?<=_PASS=)\d+' | tail -1 || echo 0)
  fail=$(echo "$output" | grep -oP '(?<=_FAIL=)\d+' | tail -1 || echo 0)
  TOTAL_PASS=$((TOTAL_PASS + pass))
  TOTAL_FAIL=$((TOTAL_FAIL + fail))
}

echo "======================================================"
echo " AEM-EVOLVE ADVERSARIAL TEST SUITE — Phase 2 (v0.4)"
echo "======================================================"
echo "skip_live = $SKIP_LIVE"
echo ""

echo "--- [1/4] Prompt Injection ---"
run_bash_test "$SCRIPT_DIR/test_prompt_injection.sh"
echo ""

echo "--- [2/4] Unauthorized Approval ---"
run_bash_test "$SCRIPT_DIR/test_unauthorized_approval.sh"
echo ""

echo "--- [3/4] Malformed Payloads ---"
run_bash_test "$SCRIPT_DIR/test_malformed_payloads.sh"
echo ""

echo "--- [4/4] Tampering Detection (no server needed) ---"
run_python_test "$SCRIPT_DIR/test_tampering_detection.py"
echo ""

echo "======================================================"
echo "TOTAL_PASS=$TOTAL_PASS"
echo "TOTAL_FAIL=$TOTAL_FAIL"
echo "TOTAL_SKIPPED=$SKIPPED"
echo ""
if [ "$TOTAL_FAIL" -eq 0 ]; then
  echo "AEM_EVOLVE_ADVERSARIAL_STATUS=PASS"
  exit 0
else
  echo "AEM_EVOLVE_ADVERSARIAL_STATUS=FAIL"
  exit 1
fi
