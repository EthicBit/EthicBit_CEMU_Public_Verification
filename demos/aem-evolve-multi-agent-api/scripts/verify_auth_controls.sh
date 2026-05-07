#!/usr/bin/env bash
# Verify RBAC auth controls for AEM-EVOLVE Multi-Agent API.
# Requires: running API at localhost:8000 (python main.py)
# Tests: 401 on missing key, 403 on wrong role, 200 on correct role.
set -euo pipefail

BASE="http://localhost:8000"
PASS_COUNT=0
FAIL_COUNT=0

check() {
  local label="$1"
  local expected_http="$2"
  local actual_http="$3"
  if [ "$actual_http" = "$expected_http" ]; then
    echo "  PASS  [$label] HTTP $actual_http"
    PASS_COUNT=$((PASS_COUNT + 1))
  else
    echo "  FAIL  [$label] expected HTTP $expected_http, got HTTP $actual_http"
    FAIL_COUNT=$((FAIL_COUNT + 1))
  fi
}

echo "=== AEM-EVOLVE MULTI-AGENT API AUTH CONTROLS VERIFICATION ==="
echo "base_url = $BASE"
echo ""

# ── 1. No key → 401 on all write/read endpoints ──────────────────────────────
echo "--- No-key checks (expect 401) ---"
check "POST /start no-key" 401 \
  "$(curl -sf -o /dev/null -w "%{http_code}" -X POST "$BASE/start" \
    -H "Content-Type: application/json" \
    -d '{"thread_id":"t-noauth"}' 2>/dev/null || echo $?)"

check "POST /approve no-key" 401 \
  "$(curl -sf -o /dev/null -w "%{http_code}" -X POST "$BASE/approve" \
    -H "Content-Type: application/json" \
    -d '{"thread_id":"t-noauth","decision":"approve"}' 2>/dev/null || echo $?)"

check "GET /status/t-noauth no-key" 401 \
  "$(curl -sf -o /dev/null -w "%{http_code}" "$BASE/status/t-noauth" 2>/dev/null || echo $?)"

# ── 2. Observer key on /approve → 403 ────────────────────────────────────────
echo ""
echo "--- Wrong-role checks (expect 403) ---"
check "POST /approve with OBSERVER key" 403 \
  "$(curl -sf -o /dev/null -w "%{http_code}" -X POST "$BASE/approve" \
    -H "X-API-Key: demo-observer-key-001" \
    -H "Content-Type: application/json" \
    -d '{"thread_id":"t-wrongrole","decision":"approve"}' 2>/dev/null || echo $?)"

check "POST /start with APPROVER key" 403 \
  "$(curl -sf -o /dev/null -w "%{http_code}" -X POST "$BASE/start" \
    -H "X-API-Key: demo-approver-key-001" \
    -H "Content-Type: application/json" \
    -d '{"thread_id":"t-wrongrole"}' 2>/dev/null || echo $?)"

check "POST /start with OBSERVER key" 403 \
  "$(curl -sf -o /dev/null -w "%{http_code}" -X POST "$BASE/start" \
    -H "X-API-Key: demo-observer-key-001" \
    -H "Content-Type: application/json" \
    -d '{"thread_id":"t-wrongrole"}' 2>/dev/null || echo $?)"

# ── 3. Correct roles → accepted (200 or 404/400 = past auth) ─────────────────
echo ""
echo "--- Correct-role checks (expect 200 or past-auth 4xx) ---"
# /start with INITIATOR key → 200 (creates session)
START_HTTP=$(curl -sf -o /dev/null -w "%{http_code}" -X POST "$BASE/start" \
    -H "X-API-Key: demo-initiator-key-001" \
    -H "Content-Type: application/json" \
    -d '{"thread_id":"t-authtest-'"$(date +%s)"'"}' 2>/dev/null || echo $?)
check "POST /start with INITIATOR key" 200 "$START_HTTP"

# /status with OBSERVER key → 200 or 404 (past auth gate = OK)
STATUS_HTTP=$(curl -sf -o /dev/null -w "%{http_code}" \
    -H "X-API-Key: demo-observer-key-001" \
    "$BASE/status/t-nonexistent" 2>/dev/null || echo $?)
if [ "$STATUS_HTTP" = "200" ] || [ "$STATUS_HTTP" = "404" ]; then
  echo "  PASS  [GET /status with OBSERVER key] HTTP $STATUS_HTTP (past auth gate)"
  PASS_COUNT=$((PASS_COUNT + 1))
else
  echo "  FAIL  [GET /status with OBSERVER key] expected 200 or 404, got $STATUS_HTTP"
  FAIL_COUNT=$((FAIL_COUNT + 1))
fi

# /chain/verify with APPROVER key → any 2xx (past auth gate)
CHAIN_HTTP=$(curl -sf -o /dev/null -w "%{http_code}" \
    -H "X-API-Key: demo-approver-key-001" \
    "$BASE/chain/verify" 2>/dev/null || echo $?)
if [ "$CHAIN_HTTP" = "200" ]; then
  echo "  PASS  [GET /chain/verify with APPROVER key] HTTP $CHAIN_HTTP"
  PASS_COUNT=$((PASS_COUNT + 1))
else
  echo "  FAIL  [GET /chain/verify with APPROVER key] expected 200, got $CHAIN_HTTP"
  FAIL_COUNT=$((FAIL_COUNT + 1))
fi

echo ""
echo "checks_passed = $PASS_COUNT"
echo "checks_failed = $FAIL_COUNT"
echo ""
if [ "$FAIL_COUNT" -eq 0 ]; then
  echo "AEM_EVOLVE_AUTH_CONTROLS_STATUS=PASS"
  echo "NOTE: Demo keys only. Not for production. No production identity provider."
else
  echo "AEM_EVOLVE_AUTH_CONTROLS_STATUS=FAIL"
  exit 1
fi
