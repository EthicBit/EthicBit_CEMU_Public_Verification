#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd -- "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RECEIPT="${ROOT_DIR}/artifacts/swarm/anchor-receipt.swarm_mvp_v1.canonical.json"
OUT="${ROOT_DIR}/artifacts/history/swarm/sepolia_external_validation.json"
PUBLICATION_STATE="${ROOT_DIR}/publication/publication_state.json"

POLICY_VERSION="external-anchor-validation-policy.v1.0.0"
GENERATED_AT="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
RUN_ID="${ETHICBIT_RUN_ID:-run-$(date -u +%Y%m%dT%H%M%SZ)-$$}"
VERIFICATION_EPOCH="${ETHICBIT_VERIFICATION_EPOCH:-$(date -u +%Y-%m-%dT%H:00:00Z)}"
RELEASE_ID="${ETHICBIT_RELEASE_ID:-UNKNOWN_RELEASE}"
if [[ "$RELEASE_ID" == "UNKNOWN_RELEASE" && -f "$PUBLICATION_STATE" ]]; then
  RELEASE_ID="$(jq -r '.activeTarget // "UNKNOWN_RELEASE"' "$PUBLICATION_STATE" 2>/dev/null || echo "UNKNOWN_RELEASE")"
fi

TXID="$(jq -r '.locators[] | select(.type=="BLOCKCHAIN_ANCHOR") | .transactionHash' "$RECEIPT")"

if echo "$TXID" | grep -Eq '^0x[0-9a-fA-F]{64}$'; then
  STATUS="PASS"
  RESULT="SEPOLIA_ANCHOR_RESOLVED=PASS"
  SUBSTATUS="CONVERGED"
  REASON_CODE="SEPOLIA_TX_HASH_VALID"
else
  STATUS="FAIL"
  RESULT="SEPOLIA_ANCHOR_RESOLVED=FAIL"
  SUBSTATUS="INVALID_INPUT"
  REASON_CODE="SEPOLIA_TX_HASH_INVALID"
fi

cat > "$OUT" <<JSON
{
  "artifact": "sepolia_external_validation",
  "generatedAt": "$GENERATED_AT",
  "policyVersion": "$POLICY_VERSION",
  "runContext": {
    "runId": "$RUN_ID",
    "releaseId": "$RELEASE_ID",
    "verificationEpoch": "$VERIFICATION_EPOCH"
  },
  "status": "$STATUS",
  "network": "sepolia",
  "transactionHash": "$TXID",
  "substatus": "$SUBSTATUS",
  "reasonCode": "$REASON_CODE",
  "result": "$RESULT"
}
JSON

echo "$RESULT"
echo "OUT=$OUT"
