#!/usr/bin/env bash
# AEM-EVOLVE Multi-Agent Governance API — Reproducible Benchmark
# Phase 3 (v0.5) — Performance, Metrics & Architecture
#
# Runs N iterations of the full governance flow and collects timing metrics
# from the /metrics endpoint.
#
# Usage:
#   bash run_benchmark.sh [iterations]
#   Default iterations: 10
#
# Requires: server running on localhost:8000, curl, python3, jq (optional)

set -euo pipefail

BASE_URL="http://127.0.0.1:8000"
INITIATOR_KEY="demo-initiator-key-001"
APPROVER_KEY="demo-approver-key-001"
OBSERVER_KEY="demo-observer-key-001"
N="${1:-10}"
PASS=0; FAIL=0

echo "======================================================"
echo " AEM-EVOLVE BENCHMARK — Phase 3 (v0.5)"
echo "======================================================"
echo "iterations = $N"
echo "base_url   = $BASE_URL"
echo ""

# 0. Health check
STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/healthz")
if [ "$STATUS" != "200" ]; then
  echo "ERROR: server not reachable at $BASE_URL (HTTP $STATUS)"
  exit 1
fi
echo "health_check = OK"
echo ""

# Reset metrics
curl -s -X POST "$BASE_URL/metrics/reset" -H "X-API-Key: $INITIATOR_KEY" > /dev/null 2>&1 || true

# 1. Run N full /start iterations
echo "--- Running $N /start iterations ---"
for i in $(seq 1 "$N"); do
  TID="bench-$(date +%s%N | tail -c 9)-$i"
  t0=$(python3 -c "import time; print(int(time.perf_counter()*1000))")
  HTTP=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$BASE_URL/start" \
    -H "Content-Type: application/json" \
    -H "X-API-Key: $INITIATOR_KEY" \
    -d "{\"thread_id\": \"$TID\", \"initial_prompt\": \"Benchmark iteration $i\"}")
  t1=$(python3 -c "import time; print(int(time.perf_counter()*1000))")
  elapsed=$((t1 - t0))
  if [ "$HTTP" = "200" ]; then
    echo "  iter $i: HTTP 200  client_elapsed_ms=${elapsed}"
    PASS=$((PASS+1))
  else
    echo "  iter $i: HTTP $HTTP  FAIL"
    FAIL=$((FAIL+1))
  fi
done

echo ""
echo "--- Running $N /approve iterations (SCOPE_LIMITED path) ---"
for i in $(seq 1 "$N"); do
  TID="bench-approve-$(date +%s%N | tail -c 9)-$i"
  # Start session first
  curl -s -o /dev/null -X POST "$BASE_URL/start" \
    -H "Content-Type: application/json" \
    -H "X-API-Key: $INITIATOR_KEY" \
    -d "{\"thread_id\": \"$TID\", \"initial_prompt\": \"Approve benchmark $i\"}" || true
  # Approve
  t0=$(python3 -c "import time; print(int(time.perf_counter()*1000))")
  HTTP=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$BASE_URL/approve" \
    -H "Content-Type: application/json" \
    -H "X-API-Key: $APPROVER_KEY" \
    -d "{\"thread_id\": \"$TID\", \"decision\": \"approve\", \"override_reason\": \"benchmark\"}")
  t1=$(python3 -c "import time; print(int(time.perf_counter()*1000))")
  elapsed=$((t1 - t0))
  echo "  approve $i: HTTP $HTTP  client_elapsed_ms=${elapsed}"
done

echo ""
echo "--- Collecting metrics from /metrics ---"
METRICS=$(curl -s "$BASE_URL/metrics" -H "X-API-Key: $OBSERVER_KEY")
echo "$METRICS" | python3 -c "
import json, sys
data = json.load(sys.stdin)
print(json.dumps(data, indent=2))
" 2>/dev/null || echo "$METRICS"

echo ""
echo "--- Health check (post-benchmark) ---"
curl -s "$BASE_URL/healthz" | python3 -c "import json,sys; print(json.dumps(json.load(sys.stdin), indent=2))"

echo ""
echo "BENCHMARK_PASS=$PASS"
echo "BENCHMARK_FAIL=$FAIL"
if [ "$FAIL" -eq 0 ]; then
  echo "AEM_EVOLVE_BENCHMARK_STATUS=PASS"
else
  echo "AEM_EVOLVE_BENCHMARK_STATUS=PARTIAL"
fi
