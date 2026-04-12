#!/usr/bin/env bash
set -euo pipefail
PAYLOAD_FILE="${1:-}"
KEY_PATH="${ETHICBIT_MLDSA_PRIVATE_KEY:-/Users/oskrmiranda/Documentos/EthicBit_CEMU/assurance/keys/mldsa_private.pem}"
[ -f "$PAYLOAD_FILE" ] || { echo "payload file not found: $PAYLOAD_FILE" >&2; exit 3; }
[ -f "$KEY_PATH" ] || { echo "mldsa private key not found: $KEY_PATH" >&2; exit 4; }
TMP_SIG="$(mktemp)"
openssl pkeyutl -sign -inkey "$KEY_PATH" -rawin -in "$PAYLOAD_FILE" -out "$TMP_SIG"
base64 < "$TMP_SIG" | tr -d '\n'
rm -f "$TMP_SIG"
