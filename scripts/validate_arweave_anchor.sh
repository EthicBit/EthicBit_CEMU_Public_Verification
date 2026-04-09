#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd -- "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RECEIPT="${ROOT_DIR}/artifacts/swarm/anchor-receipt.swarm_mvp_v1.canonical.json"
OUT="${ROOT_DIR}/artifacts/history/swarm/arweave_external_validation.json"
PUBLICATION_STATE="${ROOT_DIR}/publication/publication_state.json"
TMP_BODY="$(mktemp "/tmp/ethicbit_arweave_body.XXXXXX")"

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

TXID="$(jq -r '.locators[] | select(.type=="ARWEAVE_OBJECT") | .txId' "$RECEIPT")"
LOCATOR="$(jq -r '.locators[] | select(.type=="ARWEAVE_OBJECT") | .locator' "$RECEIPT")"

AR_META="$(curl -s --max-time 30 "https://arweave.net/tx/$TXID" || true)"
curl -sL --max-time 30 "$LOCATOR" >"$TMP_BODY" || true

META_TX_MATCH="FAIL"
META_DATA_SIZE_NONZERO="FAIL"
BODY_NONEMPTY="FAIL"
BODY_IS_JSON="FAIL"
BODY_IS_NOT_HTML="FAIL"
BODY_NO_PLACEHOLDERS="FAIL"
NOTE=""
SUBSTATUS="REACHABLE_BUT_MISMATCH"
REASON_CODE="ARWEAVE_UNRESOLVED"

META_ID="$(printf '%s' "$AR_META" | jq -r '.id // empty' 2>/dev/null || true)"
META_DATA_SIZE="$(printf '%s' "$AR_META" | jq -r '.data_size // "0"' 2>/dev/null || echo "0")"
BODY_BYTES="$(wc -c <"$TMP_BODY" | tr -d ' ')"
PLACEHOLDER_COUNT="$(rg -N -o 'PENDING_|PON_AQUI|TODO|REPLACE_ME' "$TMP_BODY" 2>/dev/null | wc -l | tr -d ' ')"

if [[ -n "$META_ID" && "$META_ID" == "$TXID" ]]; then
  META_TX_MATCH="PASS"
fi
if [[ "$META_DATA_SIZE" != "0" ]]; then
  META_DATA_SIZE_NONZERO="PASS"
fi
if [[ "${BODY_BYTES:-0}" -gt 0 ]]; then
  BODY_NONEMPTY="PASS"
fi
if jq . "$TMP_BODY" >/dev/null 2>&1; then
  BODY_IS_JSON="PASS"
fi
if ! rg -qi '<html' "$TMP_BODY"; then
  BODY_IS_NOT_HTML="PASS"
fi
if [[ "${PLACEHOLDER_COUNT:-0}" -eq 0 ]]; then
  BODY_NO_PLACEHOLDERS="PASS"
fi

if [[ "$META_TX_MATCH" == "PASS" ]] \
  && [[ "$META_DATA_SIZE_NONZERO" == "PASS" ]] \
  && [[ "$BODY_NONEMPTY" == "PASS" ]] \
  && [[ "$BODY_IS_JSON" == "PASS" ]] \
  && [[ "$BODY_IS_NOT_HTML" == "PASS" ]] \
  && [[ "$BODY_NO_PLACEHOLDERS" == "PASS" ]]; then
  STATUS="PASS"
  RESULT="ARWEAVE_OBJECT_RESOLVED=PASS"
  SUBSTATUS="CONVERGED"
  REASON_CODE="ARWEAVE_OBJECT_CONVERGED"
else
  STATUS="FAIL"
  RESULT="ARWEAVE_OBJECT_RESOLVED=FAIL"
  NOTE="Remote truth check failed: META_TX_MATCH=${META_TX_MATCH}, META_DATA_SIZE_NONZERO=${META_DATA_SIZE_NONZERO}, BODY_NONEMPTY=${BODY_NONEMPTY}, BODY_IS_JSON=${BODY_IS_JSON}, BODY_IS_NOT_HTML=${BODY_IS_NOT_HTML}, BODY_NO_PLACEHOLDERS=${BODY_NO_PLACEHOLDERS}."

  if [[ "$META_TX_MATCH" == "FAIL" ]]; then
    SUBSTATUS="HASH_MISMATCH"
    REASON_CODE="ARWEAVE_META_TX_MISMATCH"
  elif [[ "$META_DATA_SIZE_NONZERO" == "FAIL" ]]; then
    SUBSTATUS="CONTENT_UNAVAILABLE"
    REASON_CODE="ARWEAVE_DATA_SIZE_ZERO"
  elif [[ "$BODY_NONEMPTY" == "FAIL" ]]; then
    SUBSTATUS="CONTENT_UNAVAILABLE"
    REASON_CODE="ARWEAVE_BODY_EMPTY"
  elif [[ "$BODY_IS_JSON" == "FAIL" ]]; then
    SUBSTATUS="CONTENT_INVALID"
    REASON_CODE="ARWEAVE_BODY_NOT_JSON"
  elif [[ "$BODY_NO_PLACEHOLDERS" == "FAIL" ]]; then
    SUBSTATUS="CONTENT_INVALID"
    REASON_CODE="ARWEAVE_BODY_HAS_PLACEHOLDERS"
  elif [[ "$BODY_IS_NOT_HTML" == "FAIL" ]]; then
    SUBSTATUS="REACHABLE_BUT_MISMATCH"
    REASON_CODE="ARWEAVE_BODY_HTML"
  fi
fi

cat > "$OUT" <<JSON
{
  "artifact": "arweave_external_validation",
  "generatedAt": "$GENERATED_AT",
  "policyVersion": "$POLICY_VERSION",
  "runContext": {
    "runId": "$RUN_ID",
    "releaseId": "$RELEASE_ID",
    "verificationEpoch": "$VERIFICATION_EPOCH"
  },
  "status": "$STATUS",
  "txId": "$TXID",
  "locator": "$LOCATOR",
  "substatus": "$SUBSTATUS",
  "reasonCode": "$REASON_CODE",
  "checks": {
    "metaTxMatch": "$META_TX_MATCH",
    "metaDataSizeNonZero": "$META_DATA_SIZE_NONZERO",
    "bodyNonEmpty": "$BODY_NONEMPTY",
    "bodyIsJson": "$BODY_IS_JSON",
    "bodyIsNotHtml": "$BODY_IS_NOT_HTML",
    "bodyNoPlaceholders": "$BODY_NO_PLACEHOLDERS",
    "placeholderCount": ${PLACEHOLDER_COUNT:-0},
    "bodyBytes": ${BODY_BYTES:-0}
  },
  "result": "$RESULT",
  "note": "$NOTE"
}
JSON

echo "$RESULT"
echo "OUT=$OUT"
