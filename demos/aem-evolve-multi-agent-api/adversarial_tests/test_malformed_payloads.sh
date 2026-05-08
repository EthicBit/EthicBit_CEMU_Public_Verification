#!/usr/bin/env bash
# Phase 2 — Adversarial Test: Malformed Payloads
# All must return 422 (Unprocessable Entity) from Pydantic validation.
# Server must be running on localhost:8000.

set -euo pipefail

BASE_URL="http://127.0.0.1:8000"
INITIATOR_KEY="demo-initiator-key-001"
APPROVER_KEY="demo-approver-key-002"
PASS=0; FAIL=0

check() {
  local name="$1" expected="$2" actual="$3"
  if [ "$actual" = "$expected" ]; then
    echo "  PASS  [$name] HTTP $actual"
    PASS=$((PASS+1))
  else
    echo "  FAIL  [$name] expected HTTP $expected got HTTP $actual"
    FAIL=$((FAIL+1))
  fi
}

echo "=== MALFORMED PAYLOAD TESTS ==="

# MP-01: missing thread_id on /start
STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$BASE_URL/start" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $INITIATOR_KEY" \
  -d '{"initial_prompt": "test"}')
check "MP-01 missing thread_id on /start" "422" "$STATUS"

# MP-02: wrong type for thread_id (integer)
STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$BASE_URL/start" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $INITIATOR_KEY" \
  -d '{"thread_id": 12345, "initial_prompt": "test"}')
check "MP-02 integer thread_id" "422" "$STATUS"

# MP-03: invalid decision value on /approve
STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$BASE_URL/approve" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $APPROVER_KEY" \
  -d '{"thread_id": "mp-test-001", "decision": "maybe"}')
check "MP-03 invalid decision value (maybe)" "422" "$STATUS"

# MP-04: missing decision on /approve
STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$BASE_URL/approve" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $APPROVER_KEY" \
  -d '{"thread_id": "mp-test-001"}')
check "MP-04 missing decision on /approve" "422" "$STATUS"

# MP-05: completely empty body on /start
STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$BASE_URL/start" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $INITIATOR_KEY" \
  -d '{}')
check "MP-05 empty body on /start" "422" "$STATUS"

# MP-06: non-JSON body
STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$BASE_URL/start" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $INITIATOR_KEY" \
  -d 'not json at all')
check "MP-06 non-JSON body" "422" "$STATUS"

# MP-07: array instead of object
STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$BASE_URL/start" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $INITIATOR_KEY" \
  -d '["thread_id", "test"]')
check "MP-07 array body instead of object" "422" "$STATUS"

echo ""
echo "MALFORMED_PAYLOAD_PASS=$PASS"
echo "MALFORMED_PAYLOAD_FAIL=$FAIL"
if [ "$FAIL" -eq 0 ]; then
  echo "MALFORMED_PAYLOAD_STATUS=PASS"
else
  echo "MALFORMED_PAYLOAD_STATUS=FAIL"
fi
