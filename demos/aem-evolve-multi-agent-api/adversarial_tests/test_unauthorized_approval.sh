#!/usr/bin/env bash
# Phase 2 — Adversarial Test: Unauthorized Approval Attempts
# All must fail closed: 401 (no/invalid key) or 403 (wrong role).
# Server must be running on localhost:8000.

set -euo pipefail

BASE_URL="http://127.0.0.1:8000"
INITIATOR_KEY="demo-initiator-key-001"
OBSERVER_KEY="demo-observer-key-003"
PASS=0; FAIL=0

check() {
  local name="$1" expected="$2" actual="$3"
  if [ "$actual" = "$expected" ]; then
    echo "  PASS  [$name] HTTP $actual (fail-closed)"
    PASS=$((PASS+1))
  else
    echo "  FAIL  [$name] expected HTTP $expected got HTTP $actual"
    FAIL=$((FAIL+1))
  fi
}

echo "=== UNAUTHORIZED APPROVAL ATTEMPTS ==="

# UA-01: no X-API-Key header
STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$BASE_URL/approve" \
  -H "Content-Type: application/json" \
  -d '{"thread_id": "ua-test-001", "decision": "approve"}')
check "UA-01 no X-API-Key" "401" "$STATUS"

# UA-02: empty X-API-Key
STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$BASE_URL/approve" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: " \
  -d '{"thread_id": "ua-test-001", "decision": "approve"}')
check "UA-02 empty X-API-Key" "401" "$STATUS"

# UA-03: invalid/unknown key
STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$BASE_URL/approve" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: not-a-real-key-xyz-123" \
  -d '{"thread_id": "ua-test-001", "decision": "approve"}')
check "UA-03 invalid key" "401" "$STATUS"

# UA-04: INITIATOR key on /approve (wrong role)
STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$BASE_URL/approve" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $INITIATOR_KEY" \
  -d '{"thread_id": "ua-test-001", "decision": "approve"}')
check "UA-04 INITIATOR key on /approve" "403" "$STATUS"

# UA-05: OBSERVER key on /approve (wrong role)
STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$BASE_URL/approve" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OBSERVER_KEY" \
  -d '{"thread_id": "ua-test-001", "decision": "approve"}')
check "UA-05 OBSERVER key on /approve" "403" "$STATUS"

# UA-06: INITIATOR key on /start with OBSERVER key (wrong role for /start attempted)
STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$BASE_URL/start" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OBSERVER_KEY" \
  -d '{"thread_id": "ua-test-002", "initial_prompt": "test"}')
check "UA-06 OBSERVER key on /start" "403" "$STATUS"

echo ""
echo "UNAUTHORIZED_APPROVAL_PASS=$PASS"
echo "UNAUTHORIZED_APPROVAL_FAIL=$FAIL"
if [ "$FAIL" -eq 0 ]; then
  echo "UNAUTHORIZED_APPROVAL_STATUS=PASS"
else
  echo "UNAUTHORIZED_APPROVAL_STATUS=FAIL"
fi
