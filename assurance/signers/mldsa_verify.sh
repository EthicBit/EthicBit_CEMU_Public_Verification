#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd -- "${SCRIPT_DIR}/../.." && pwd)"

LEVEL="${ETHICBIT_MLDSA_LEVEL:-65}"
PUBKEY_PATH="${ETHICBIT_MLDSA_PUBLIC_KEY:-${REPO_ROOT}/assurance/keys/mldsa_public.pem}"

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
      echo "ERROR: unknown option: $1" >&2
      exit 2
      ;;
    *)
      break
      ;;
  esac
done

PAYLOAD_FILE="${1:-}"
SIGNATURE_B64="${2:-}"

[ -f "$PAYLOAD_FILE" ] || { echo "ERROR: payload file not found" >&2; exit 3; }
[ -n "$SIGNATURE_B64" ] || { echo "ERROR: no signature provided" >&2; exit 5; }
[ -n "$LEVEL" ] || { echo "ERROR: invalid level" >&2; exit 7; }
[ -f "$PUBKEY_PATH" ] || { echo "ERROR: mldsa public key not found: $PUBKEY_PATH" >&2; exit 4; }

# Decodificar base64
TMP_SIG="$(mktemp)"
cleanup() { rm -f "$TMP_SIG"; }
trap cleanup EXIT

if ! printf "%s" "$SIGNATURE_B64" | base64 --decode > "$TMP_SIG" 2>/dev/null; then
  if ! printf "%s" "$SIGNATURE_B64" | base64 -d > "$TMP_SIG" 2>/dev/null; then
    if ! printf "%s" "$SIGNATURE_B64" | base64 -D > "$TMP_SIG" 2>/dev/null; then
      echo "ERROR: invalid base64 signature" >&2
      exit 6
    fi
  fi
fi

if openssl pkeyutl -verify -pubin -inkey "$PUBKEY_PATH" -rawin -in "$PAYLOAD_FILE" -sigfile "$TMP_SIG" >/dev/null 2>&1; then
  echo "PASS"
  exit 0
fi

echo "FAIL"
exit 1
