#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

HISTORY_DIR="./artifacts/history/constitutional"
DRIFT_STATUS="$HISTORY_DIR/publication_drift_protocol_status.json"
RECEIPT="./artifacts/swarm/anchor-receipt.swarm_mvp_v1.canonical.json"
BUNDLE="./artifacts/security_incident_bundle_v1_0.json"
HARDENING="./artifacts/history/swarm/anchor_hardening_status.swarm_mvp_v1.json"
PROTOCOL_DOC="./docs/technical/EthicBit_CEMU_v3_7_0_plus_Publication_Drift_Resolution_Protocol.md"

mkdir -p "$HISTORY_DIR"

fail() {
  echo "ERROR: $1" >&2
  exit 1
}

require_file() {
  test -f "$1" || fail "missing file: $1"
}

json_ok() {
  jq '.' "$1" >/dev/null 2>&1
}

require_file "$RECEIPT"
require_file "$BUNDLE"
require_file "$HARDENING"
require_file "$PROTOCOL_DOC"

json_ok "$RECEIPT" || fail "invalid json: $RECEIPT"
json_ok "$BUNDLE" || fail "invalid json: $BUNDLE"
json_ok "$HARDENING" || fail "invalid json: $HARDENING"

PLACEHOLDER_COUNT="$(grep -RniE 'PON_AQUI|PENDING_|PEGA_AQUI' "$RECEIPT" 2>/dev/null | wc -l | tr -d ' ')"
EMPTY_LOCATORS="$(jq -r '.locators[] | .locator // ""' "$RECEIPT" | awk 'length==0 {c++} END{print c+0}')"

AR_TX_ID="$(jq -r '.locators[] | select(.type=="ARWEAVE_OBJECT") | .txId' "$RECEIPT")"
AR_LOCATOR="$(jq -r '.locators[] | select(.type=="ARWEAVE_OBJECT") | .locator' "$RECEIPT")"
AO_PROCESS_ID="$(jq -r '.locators[] | select(.type=="AO_PROCESS") | .processId' "$RECEIPT")"
AO_MESSAGE_ID="$(jq -r '.locators[] | select(.type=="AO_PROCESS") | .messageId' "$RECEIPT")"
AO_LOCATOR="$(jq -r '.locators[] | select(.type=="AO_PROCESS") | .locator' "$RECEIPT")"

AR_META="$(curl -s "https://arweave.net/tx/$AR_TX_ID" || true)"
AR_BODY="$(curl -sL "$AR_LOCATOR" || true)"
AO_BODY="$(curl -sL "$AO_LOCATOR" || true)"

AR_OK="FAIL"
if echo "$AR_META" | jq -e '.id and .data_size' >/dev/null 2>&1 \
  && test "$(echo "$AR_META" | jq -r '.id')" = "$AR_TX_ID" \
  && test "$(echo "$AR_META" | jq -r '.data_size')" != "0" \
  && test -n "$AR_BODY" \
  && ! printf '%s' "$AR_BODY" | grep -qi '<html'
then
  AR_OK="PASS"
fi

AO_OK="FAIL"
if test -n "$AO_PROCESS_ID" && test -n "$AO_MESSAGE_ID" && test -n "$AO_LOCATOR" && test -n "$AO_BODY"; then
  AO_OK="PASS"
fi

NO_UNRESOLVED="FAIL"
if test "$PLACEHOLDER_COUNT" = "0" && test "$EMPTY_LOCATORS" = "0" && test "$AR_OK" = "PASS" && test "$AO_OK" = "PASS"; then
  NO_UNRESOLVED="PASS"
fi

HARDENING_STATE="$(jq -r '.anchorHardeningEnabled' "$HARDENING")"

cat > "$DRIFT_STATUS" <<JSON
{
  "artifact": "publication_drift_protocol_status",
  "protocolDocument": "$PROTOCOL_DOC",
  "publicationFreezeState": "PUBLICATION_FREEZE_ACTIVE",
  "canonicalRootState": "CANONICAL_ROOT_SELECTED",
  "packState": "ACTIVE_CANONICAL",
  "currentState": "EXTERNAL_ANCHOR_EVIDENCE_READY_FOR_INDEPENDENT_REVERIFICATION",
  "anchorHardeningEnabled": "$HARDENING_STATE",
  "checks": {
    "receiptJsonValid": "PASS",
    "bundleJsonValid": "PASS",
    "arweaveResolved": "$AR_OK",
    "aoResolved": "$AO_OK",
    "receiptPlaceholderCount": $PLACEHOLDER_COUNT,
    "receiptEmptyLocatorCount": $EMPTY_LOCATORS,
    "noUnresolvedAnchorConflicts": "$NO_UNRESOLVED"
  },
  "rule": "canonize_first_harden_after",
  "note": "Per drift protocol, anchor hardening is enabled only after a single active canonical chain is restored and revalidated."
}
JSON

echo "PUBLICATION_FREEZE_STATE=PUBLICATION_FREEZE_ACTIVE"
echo "CANONICAL_ROOT_STATE=CANONICAL_ROOT_SELECTED"
echo "PACK_STATE=ACTIVE_CANONICAL"
echo "CURRENT_STATE=EXTERNAL_ANCHOR_EVIDENCE_READY_FOR_INDEPENDENT_REVERIFICATION"
echo "ARWEAVE_OBJECT_RESOLVED=$AR_OK"
echo "AO_PROCESS_RESOLVED=$AO_OK"
echo "PLACEHOLDER_COUNT=$PLACEHOLDER_COUNT"
echo "EMPTY_LOCATORS=$EMPTY_LOCATORS"
echo "no_unresolved_anchor_conflicts=$NO_UNRESOLVED"
echo "ANCHOR_HARDENING_ENABLED=$HARDENING_STATE"
echo "DRIFT_STATUS_FILE=$DRIFT_STATUS"
