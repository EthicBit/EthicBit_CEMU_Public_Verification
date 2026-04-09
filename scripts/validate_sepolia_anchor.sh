#!/bin/sh
set -eu

REPO_ROOT="${1:-/Users/oskrmiranda/Documentos/EthicBit_CEMU}"
RECEIPT="$REPO_ROOT/artifacts/swarm/anchor-receipt.swarm_mvp_v1.canonical.json"
OUT="$REPO_ROOT/artifacts/history/swarm/sepolia_external_validation.json"

mkdir -p "$(dirname "$OUT")"

NETWORK="$(jq -r '.locators[] | select(.type=="BLOCKCHAIN_ANCHOR") | .network // "MISSING"' "$RECEIPT")"
CHAIN_ID="$(jq -r '.locators[] | select(.type=="BLOCKCHAIN_ANCHOR") | .chainId // "MISSING"' "$RECEIPT")"
TX_HASH="$(jq -r '.locators[] | select(.type=="BLOCKCHAIN_ANCHOR") | .transactionHash // "MISSING"' "$RECEIPT")"
BLOCK_HASH="$(jq -r '.locators[] | select(.type=="BLOCKCHAIN_ANCHOR") | .blockHash // "MISSING"' "$RECEIPT")"
BLOCK_NUMBER="$(jq -r '.locators[] | select(.type=="BLOCKCHAIN_ANCHOR") | .blockNumber // "MISSING"' "$RECEIPT")"

STATUS="FAIL"
if [ "$NETWORK" = "Sepolia" ] && [ "$CHAIN_ID" = "11155111" ] && \
   [ "$TX_HASH" != "MISSING" ] && [ "$BLOCK_HASH" != "MISSING" ] && \
   [ "$BLOCK_NUMBER" != "MISSING" ]; then
  STATUS="PASS"
fi

cat > "$OUT" <<EOF
{
  "anchor_type": "BLOCKCHAIN_ANCHOR",
  "network": "$NETWORK",
  "chainId": $CHAIN_ID,
  "transactionHash": "$TX_HASH",
  "blockHash": "$BLOCK_HASH",
  "blockNumber": $BLOCK_NUMBER,
  "resolved": "$STATUS"
}
EOF

echo "SEPOLIA_ANCHOR_RESOLVED=$STATUS"
echo "OUT=$OUT"
