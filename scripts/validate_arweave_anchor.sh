#!/bin/sh
set -eu

REPO_ROOT="${1:-/Users/oskrmiranda/Documentos/EthicBit_CEMU}"
RECEIPT="$REPO_ROOT/artifacts/swarm/anchor-receipt.swarm_mvp_v1.canonical.json"
OUT="$REPO_ROOT/artifacts/history/swarm/arweave_external_validation.json"
TMP_RAW="/tmp/arweave_validation.raw"

mkdir -p "$(dirname "$OUT")"

TXID="$(jq -r '.locators[] | select(.type=="ARWEAVE_OBJECT") | .txId // "MISSING"' "$RECEIPT")"
LOCATOR="$(jq -r '.locators[] | select(.type=="ARWEAVE_OBJECT") | .locator // "MISSING"' "$RECEIPT")"

HTML_DETECTED="true"
JSON_PARSE="FAIL"
RESOLVED="FAIL"

if [ "$LOCATOR" != "MISSING" ]; then
  curl -sL "$LOCATOR" > "$TMP_RAW" || true

  if grep -qi '<html' "$TMP_RAW"; then
    HTML_DETECTED="true"
  else
    HTML_DETECTED="false"
  fi

  if jq . "$TMP_RAW" >/dev/null 2>&1; then
    JSON_PARSE="PASS"
  fi

  if [ "$HTML_DETECTED" = "false" ] && [ "$JSON_PARSE" = "PASS" ]; then
    RESOLVED="PASS"
  fi
fi

cat > "$OUT" <<EOF
{
  "anchor_type": "ARWEAVE_OBJECT",
  "candidate_id": "$TXID",
  "candidate_locator": "$LOCATOR",
  "resolved": "$RESOLVED",
  "html_detected": $HTML_DETECTED,
  "json_parse": "$JSON_PARSE"
}
EOF

echo "ARWEAVE_OBJECT_RESOLVED=$RESOLVED"
echo "OUT=$OUT"
