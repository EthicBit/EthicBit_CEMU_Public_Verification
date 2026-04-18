#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd -- "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RECEIPT="${ROOT_DIR}/artifacts/swarm/anchor-receipt.swarm_mvp_v1.canonical.json"
OUT="${ROOT_DIR}/artifacts/history/swarm/ao_external_validation.json"
PUBLICATION_STATE="${ROOT_DIR}/publication/publication_state.json"
TMP_BODY="$(mktemp "/tmp/ethicbit_ao_body.XXXXXX")"

cleanup() {
  rm -f "$TMP_BODY"
}
trap cleanup EXIT

POLICY_VERSION="external-anchor-validation-policy.v1.0.0"
GENERATED_AT="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
RUN_ID="${ETHICBIT_RUN_ID:-run-$(date -u +%Y%m%dT%H%M%SZ)-$$}"
VERIFICATION_EPOCH="${ETHICBIT_VERIFICATION_EPOCH:-$(date -u +%Y-%m-%dT%H:00:00Z)}"
RELEASE_ID="${ETHICBIT_RELEASE_ID:-UNKNOWN_RELEASE}"
if [[ "$RELEASE_ID" == "UNKNOWN_RELEASE" && -f "$PUBLICATION_STATE" ]]; then
  RELEASE_ID="$(jq -r '.activeTarget // "UNKNOWN_RELEASE"' "$PUBLICATION_STATE" 2>/dev/null || echo "UNKNOWN_RELEASE")"
fi

PROCESS_ID="$(jq -r '.locators[] | select(.type=="AO_PROCESS") | .processId' "$RECEIPT")"
MESSAGE_ID="$(jq -r '.locators[] | select(.type=="AO_PROCESS") | .messageId' "$RECEIPT")"
PRIMARY_LOCATOR="$(jq -r '.locators[] | select(.type=="AO_PROCESS") | .locator' "$RECEIPT")"

CANDIDATES=(
  "$PRIMARY_LOCATOR"
  "https://su-router.ao-testnet.xyz/${MESSAGE_ID}?process-id=${PROCESS_ID}"
  "https://cu.ao-testnet.xyz/result/${MESSAGE_ID}?process-id=${PROCESS_ID}"
)

AO_OK="FAIL"
SELECTED_LOCATOR=""
SELECTED_HTTP="000"
SELECTED_BYTES=0
SELECTED_BODY_CLASS="EMPTY"
NOTE="No AO endpoint returned a valid live payload."
SUBSTATUS="REACHABLE_BUT_MISMATCH"
REASON_CODE="AO_UNRESOLVED"

for candidate in "${CANDIDATES[@]}"; do
  [[ -n "$candidate" && "$candidate" != "null" ]] || continue

  HTTP_CODE="$(curl -sS -L --max-time 30 -o "$TMP_BODY" -w '%{http_code}' "$candidate" || echo "000")"
  BODY_BYTES="$(wc -c <"$TMP_BODY" | tr -d ' ')"

  BODY_CLASS="TEXT"
  if [[ "${BODY_BYTES:-0}" -eq 0 ]]; then
    BODY_CLASS="EMPTY"
  elif rg -qi '<html' "$TMP_BODY"; then
    BODY_CLASS="HTML"
  elif rg -qi 'not found|process scheduler not found|unable to locate process|upstream timeout|error' "$TMP_BODY"; then
    BODY_CLASS="ERROR_TEXT"
  fi

  SELECTED_LOCATOR="$candidate"
  SELECTED_HTTP="$HTTP_CODE"
  SELECTED_BYTES="${BODY_BYTES:-0}"
  SELECTED_BODY_CLASS="$BODY_CLASS"

  if [[ "$HTTP_CODE" =~ ^2[0-9][0-9]$ ]] && [[ "$BODY_CLASS" == "TEXT" ]]; then
    AO_OK="PASS"
    NOTE="AO endpoint resolved successfully with non-HTML payload."
    break
  fi
done

if [[ "$AO_OK" == "PASS" ]]; then
  STATUS="PASS"
  RESULT="AO_PROCESS_RESOLVED=PASS"
  SUBSTATUS="CONVERGED"
  REASON_CODE="AO_PAYLOAD_RESOLVED"
else
  STATUS="FAIL"
  RESULT="AO_PROCESS_RESOLVED=FAIL"
  NOTE="${NOTE} Last probe: http=${SELECTED_HTTP}, bodyClass=${SELECTED_BODY_CLASS}, locator=${SELECTED_LOCATOR}."

  if [[ "$SELECTED_HTTP" == "404" ]]; then
    SUBSTATUS="RESOLUTION_FAILED"
    REASON_CODE="AO_HTTP_404"
  elif [[ "$SELECTED_HTTP" == "000" ]]; then
    SUBSTATUS="RESOLUTION_FAILED"
    REASON_CODE="AO_TRANSPORT_ERROR"
  elif [[ "$SELECTED_BODY_CLASS" == "EMPTY" ]]; then
    SUBSTATUS="CONTENT_UNAVAILABLE"
    REASON_CODE="AO_EMPTY_PAYLOAD"
  elif [[ "$SELECTED_BODY_CLASS" == "HTML" ]]; then
    SUBSTATUS="REACHABLE_BUT_MISMATCH"
    REASON_CODE="AO_HTML_PAYLOAD"
  elif [[ "$SELECTED_BODY_CLASS" == "ERROR_TEXT" ]]; then
    SUBSTATUS="REACHABLE_BUT_MISMATCH"
    REASON_CODE="AO_ERROR_PAYLOAD"
  fi
fi

cat > "$OUT" <<JSON
{
  "artifact": "ao_external_validation",
  "generatedAt": "$GENERATED_AT",
  "policyVersion": "$POLICY_VERSION",
  "runContext": {
    "runId": "$RUN_ID",
    "releaseId": "$RELEASE_ID",
    "verificationEpoch": "$VERIFICATION_EPOCH"
  },
  "status": "$STATUS",
  "processId": "$PROCESS_ID",
  "messageId": "$MESSAGE_ID",
  "locator": "$PRIMARY_LOCATOR",
  "selectedLocator": "$SELECTED_LOCATOR",
  "substatus": "$SUBSTATUS",
  "reasonCode": "$REASON_CODE",
  "checks": {
    "httpCode": "$SELECTED_HTTP",
    "bodyBytes": ${SELECTED_BYTES:-0},
    "bodyClass": "$SELECTED_BODY_CLASS"
  },
  "result": "$RESULT",
  "note": "$NOTE"
}
JSON

echo "$RESULT"
echo "OUT=$OUT"
