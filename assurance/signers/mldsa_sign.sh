#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd -- "${SCRIPT_DIR}/../.." && pwd)"

LEVEL="${ETHICBIT_MLDSA_LEVEL:-65}"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --level)
      LEVEL="${2:-}"
      shift 2
      ;;
    --)
      shift
      break
      ;;
    -*)
      echo "unknown option: $1" >&2
      exit 2
      ;;
    *)
      break
      ;;
  esac
done

PAYLOAD_FILE="${1:-}"
KEY_PATH="${ETHICBIT_MLDSA_PRIVATE_KEY:-${REPO_ROOT}/assurance/keys/mldsa_private.pem}"
[ -f "$PAYLOAD_FILE" ] || { echo "payload file not found: $PAYLOAD_FILE" >&2; exit 3; }
[ -f "$KEY_PATH" ] || { echo "mldsa private key not found: $KEY_PATH" >&2; exit 4; }
[ -n "$LEVEL" ] || { echo "invalid ML-DSA level" >&2; exit 5; }
TMP_SIG="$(mktemp)"
openssl pkeyutl -sign -inkey "$KEY_PATH" -rawin -in "$PAYLOAD_FILE" -out "$TMP_SIG"
base64 < "$TMP_SIG" | tr -d '\n'
rm -f "$TMP_SIG"
