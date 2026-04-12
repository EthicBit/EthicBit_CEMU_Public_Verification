#!/usr/bin/env bash
set -euo pipefail
PAYLOAD_FILE="${1:-}"
SIGNATURE_B64="${2:-}"
PUBKEY_PATH="${ETHICBIT_MLDSA_PUBLIC_KEY:-/Users/oskrmiranda/Documentos/EthicBit_CEMU/assurance/keys/mldsa_public.pem}"
[ -f "$PAYLOAD_FILE" ] || { echo "payload file not found: $PAYLOAD_FILE" >&2; exit 3; }
[ -f "$PUBKEY_PATH" ] || { echo "mldsa public key not found: $PUBKEY_PATH" >&2; exit 4; }
TMP_SIG="$(mktemp)"
printf "%s" "$SIGNATURE_B64" | base64 --decode > "$TMP_SIG"
if openssl pkeyutl -verify -pubin -inkey "$PUBKEY_PATH" -rawin -in "$PAYLOAD_FILE" -sigfile "$TMP_SIG" >/dev/null 2>&1; then
  echo "PASS"
  RC=0
else
  echo "FAIL"
  RC=1
fi
rm -f "$TMP_SIG"
exit "$RC"
