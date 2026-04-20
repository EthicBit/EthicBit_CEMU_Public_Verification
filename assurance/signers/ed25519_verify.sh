#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd -- "${SCRIPT_DIR}/../.." && pwd)"

if [[ $# -ne 2 ]]; then
  echo "usage: $(basename "$0") <payload-file> <signature-b64>" >&2
  exit 2
fi

PAYLOAD_FILE="$1"
SIGNATURE_B64="$2"
PUBKEY_PATH="${ETHICBIT_ED25519_PUBLIC_KEY:-${REPO_ROOT}/assurance/keys/ed25519_public.pem}"
[ -f "$PAYLOAD_FILE" ] || { echo "payload file not found: $PAYLOAD_FILE" >&2; exit 3; }
[ -f "$PUBKEY_PATH" ] || { echo "ed25519 public key not found: $PUBKEY_PATH" >&2; exit 4; }
TMP_SIG="$(mktemp)"
if ! printf "%s" "$SIGNATURE_B64" | base64 --decode > "$TMP_SIG" 2>/dev/null; then
  if ! printf "%s" "$SIGNATURE_B64" | base64 -d > "$TMP_SIG" 2>/dev/null; then
    if ! printf "%s" "$SIGNATURE_B64" | base64 -D > "$TMP_SIG" 2>/dev/null; then
      echo "invalid base64 signature" >&2
      rm -f "$TMP_SIG"
      exit 6
    fi
  fi
fi
if openssl pkeyutl -verify -pubin -inkey "$PUBKEY_PATH" -rawin -in "$PAYLOAD_FILE" -sigfile "$TMP_SIG" >/dev/null 2>&1; then
  echo "PASS"
  RC=0
else
  echo "FAIL"
  RC=1
fi
rm -f "$TMP_SIG"
exit "$RC"
