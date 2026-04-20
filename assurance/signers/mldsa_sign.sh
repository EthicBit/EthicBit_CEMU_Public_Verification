#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd -- "${SCRIPT_DIR}/../.." && pwd)"

LEVEL="${ETHICBIT_MLDSA_LEVEL:-65}"
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
      echo "unknown option: $1" >&2
      exit 2
      ;;
    *)
      break
      ;;
  esac
done

if [[ $# -ne 1 ]]; then
  echo "usage: $(basename "$0") [--level <n>] <payload-file>" >&2
  exit 2
fi

PAYLOAD_FILE="$1"
KEY_PATH="${ETHICBIT_MLDSA_PRIVATE_KEY:-${REPO_ROOT}/assurance/keys/mldsa_private.pem}"
[ -f "$PAYLOAD_FILE" ] || { echo "payload file not found: $PAYLOAD_FILE" >&2; exit 3; }
[ -f "$KEY_PATH" ] || { echo "mldsa private key not found: $KEY_PATH" >&2; exit 4; }
[ -n "$LEVEL" ] || { echo "invalid ML-DSA level" >&2; exit 5; }

MODE="$(printf '%s' "$MLDSA_EFFECTIVE_MODE" | tr '[:upper:]' '[:lower:]')"
if as_bool "$REQUIRE_NATIVE_HYBRID"; then
  if [[ "$MODE" != "native" && "$MODE" != "native_mldsa" ]]; then
    echo "mldsa signer policy violation: native hybrid required but effective mode is '$MLDSA_EFFECTIVE_MODE'" >&2
    exit 8
  fi
fi

# Keep key id taxonomy coherent with effective mode to avoid semantic drift.
if [[ -n "$MLDSA_KEY_ID" ]]; then
  if [[ "$MODE" == "compatibility_fallback" && "$MLDSA_KEY_ID" != *COMPAT* ]]; then
    echo "mldsa signer policy violation: compatibility_fallback requires COMPAT key id, got '$MLDSA_KEY_ID'" >&2
    exit 9
  fi
  if [[ ( "$MODE" == "native" || "$MODE" == "native_mldsa" ) && "$MLDSA_KEY_ID" == *COMPAT* ]]; then
    echo "mldsa signer policy violation: native mode cannot use COMPAT key id '$MLDSA_KEY_ID'" >&2
    exit 10
  fi
fi

TMP_SIG="$(mktemp)"
openssl pkeyutl -sign -inkey "$KEY_PATH" -rawin -in "$PAYLOAD_FILE" -out "$TMP_SIG"
base64 < "$TMP_SIG" | tr -d '\n'
rm -f "$TMP_SIG"
