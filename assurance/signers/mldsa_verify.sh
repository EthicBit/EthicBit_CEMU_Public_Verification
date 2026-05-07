#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd -- "${SCRIPT_DIR}/../.." && pwd)"

LEVEL="${ETHICBIT_MLDSA_LEVEL:-65}"
PUBKEY_PATH="${ETHICBIT_MLDSA_PUBLIC_KEY:-${REPO_ROOT}/assurance/keys/mldsa_public.pem}"
MLDSA_EFFECTIVE_MODE="${ETHICBIT_MLDSA_EFFECTIVE_MODE:-${ETHICBIT_MLDSA_MODE:-unknown}}"
REQUIRE_NATIVE_HYBRID="${ETHICBIT_REQUIRE_NATIVE_HYBRID:-0}"
MLDSA_KEY_ID="${ETHICBIT_MLDSA_KEY_ID:-}"

as_bool() {
  local raw
  raw="$(printf '%s' "${1:-}" | tr '[:upper:]' '[:lower:]')"
  [[ "$raw" == "1" || "$raw" == "true" || "$raw" == "yes" || "$raw" == "y" || "$raw" == "on" ]]
}

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

if [[ $# -ne 2 ]]; then
  echo "usage: $(basename "$0") [--level <n>] <payload-file> <signature-b64>" >&2
  exit 2
fi

PAYLOAD_FILE="$1"
SIGNATURE_B64="$2"

[ -f "$PAYLOAD_FILE" ] || { echo "ERROR: payload file not found" >&2; exit 3; }
[ -n "$SIGNATURE_B64" ] || { echo "ERROR: no signature provided" >&2; exit 5; }
[ -n "$LEVEL" ] || { echo "ERROR: invalid level" >&2; exit 7; }
[ -f "$PUBKEY_PATH" ] || { echo "ERROR: mldsa public key not found: $PUBKEY_PATH" >&2; exit 4; }

MODE="$(printf '%s' "$MLDSA_EFFECTIVE_MODE" | tr '[:upper:]' '[:lower:]')"
if as_bool "$REQUIRE_NATIVE_HYBRID"; then
  if [[ "$MODE" != "native" && "$MODE" != "native_mldsa" ]]; then
    echo "ERROR: mldsa verifier policy violation: native hybrid required but effective mode is '$MLDSA_EFFECTIVE_MODE'" >&2
    exit 8
  fi
fi

# Keep key id taxonomy coherent with effective mode to avoid semantic drift.
if [[ -n "$MLDSA_KEY_ID" ]]; then
  if [[ "$MODE" == "compatibility_fallback" && "$MLDSA_KEY_ID" != *COMPAT* ]]; then
    echo "ERROR: mldsa verifier policy violation: compatibility_fallback requires COMPAT key id, got '$MLDSA_KEY_ID'" >&2
    exit 9
  fi
  if [[ ( "$MODE" == "native" || "$MODE" == "native_mldsa" ) && "$MLDSA_KEY_ID" == *COMPAT* ]]; then
    echo "ERROR: mldsa verifier policy violation: native mode cannot use COMPAT key id '$MLDSA_KEY_ID'" >&2
    exit 10
  fi
fi

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
