#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd -- "${SCRIPT_DIR}/../.." && pwd)"

PAYLOAD_FILE="${1:-}"
KEY_PATH="${ETHICBIT_ED25519_PRIVATE_KEY:-${REPO_ROOT}/assurance/keys/ed25519_private.pem}"
[ -f "$PAYLOAD_FILE" ] || { echo "payload file not found: $PAYLOAD_FILE" >&2; exit 3; }
[ -f "$KEY_PATH" ] || { echo "ed25519 private key not found: $KEY_PATH" >&2; exit 4; }
TMP_SIG="$(mktemp)"
openssl pkeyutl -sign -inkey "$KEY_PATH" -rawin -in "$PAYLOAD_FILE" -out "$TMP_SIG"
base64 < "$TMP_SIG" | tr -d '\n'
rm -f "$TMP_SIG"
