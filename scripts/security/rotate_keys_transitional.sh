#!/usr/bin/env bash
# Transitional key rotation for EthicBit signing.
# - Generates fresh key material for GitHub Secrets mode.
# - Does not rewrite git history.
# - Produces actionable `gh secret set` commands.
#
# Usage:
#   scripts/security/rotate_keys_transitional.sh [--output-dir <dir>] [--allow-compat-mldsa-ed25519]
#
# Notes:
# - Default behavior is strict: ML-DSA key generation must be available locally.
# - If OpenSSL lacks ML-DSA support, pass --allow-compat-mldsa-ed25519 to generate a temporary
#   compatibility key for ETHICBIT_MLDSA_* secrets. This is not sovereign-grade.

set -euo pipefail
umask 077

SCRIPT_NAME="$(basename "$0")"
REPO_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)"
TS="$(date -u +%Y%m%dT%H%M%SZ)"

OUTPUT_DIR=""
ALLOW_COMPAT_MLDSA_ED25519="0"

usage() {
  cat >&2 <<EOF
Usage:
  ${SCRIPT_NAME} [--output-dir <dir>] [--allow-compat-mldsa-ed25519]

Options:
  --output-dir <dir>             Output directory for generated key bundle.
                                 Default: ${REPO_ROOT}/artifacts/security/key_rotation_transitional/${TS}
  --allow-compat-mldsa-ed25519   Allow temporary ED25519 compatibility key for ETHICBIT_MLDSA_* secrets
                                 when native ML-DSA generation is unavailable.
EOF
  exit 2
}

die() {
  echo "ERROR: $*" >&2
  exit 1
}

as_bool() {
  local raw="${1:-}"
  raw="$(printf '%s' "$raw" | tr '[:upper:]' '[:lower:]')"
  [[ "$raw" == "1" || "$raw" == "true" || "$raw" == "yes" || "$raw" == "y" || "$raw" == "on" ]]
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --output-dir)
      [[ $# -ge 2 ]] || usage
      OUTPUT_DIR="$2"
      shift 2
      ;;
    --allow-compat-mldsa-ed25519)
      ALLOW_COMPAT_MLDSA_ED25519="1"
      shift
      ;;
    -h|--help)
      usage
      ;;
    *)
      usage
      ;;
  esac
done

command -v openssl >/dev/null 2>&1 || die "openssl is required"
command -v python3 >/dev/null 2>&1 || die "python3 is required"
command -v git >/dev/null 2>&1 || die "git is required"

if [[ -z "$OUTPUT_DIR" ]]; then
  OUTPUT_DIR="${REPO_ROOT}/artifacts/security/key_rotation_transitional/${TS}"
fi

mkdir -p "$OUTPUT_DIR"
chmod 700 "$OUTPUT_DIR"

ED25519_PRIV="${OUTPUT_DIR}/ed25519_private.pem"
ED25519_PUB="${OUTPUT_DIR}/ed25519_public.pem"
MLDSA_PRIV="${OUTPUT_DIR}/mldsa_private.pem"
MLDSA_PUB="${OUTPUT_DIR}/mldsa_public.pem"
META_PATH="${OUTPUT_DIR}/rotation_metadata.json"

echo "Generating ED25519 keypair..."
openssl genpkey -algorithm Ed25519 -out "$ED25519_PRIV"
openssl pkey -in "$ED25519_PRIV" -pubout -out "$ED25519_PUB"

mldsa_generation_mode="native_mldsa"

echo "Generating ML-DSA keypair..."
if openssl genpkey -algorithm ML-DSA-65 -out "$MLDSA_PRIV" >/tmp/ethicbit_mldsa_gen.log 2>&1; then
  openssl pkey -in "$MLDSA_PRIV" -pubout -out "$MLDSA_PUB"
else
  if as_bool "$ALLOW_COMPAT_MLDSA_ED25519"; then
    echo "WARN: ML-DSA generation unavailable; using ED25519 compatibility key for ETHICBIT_MLDSA_* secrets." >&2
    mldsa_generation_mode="compatibility_fallback_ed25519"
    openssl genpkey -algorithm Ed25519 -out "$MLDSA_PRIV"
    openssl pkey -in "$MLDSA_PRIV" -pubout -out "$MLDSA_PUB"
  else
    cat /tmp/ethicbit_mldsa_gen.log >&2 || true
    die "ML-DSA generation failed. Re-run with --allow-compat-mldsa-ed25519 only for temporary non-sovereign operation."
  fi
fi
rm -f /tmp/ethicbit_mldsa_gen.log

chmod 600 "$ED25519_PRIV" "$MLDSA_PRIV"
chmod 644 "$ED25519_PUB" "$MLDSA_PUB"

tracked_private_hits="$(
  cd "$REPO_ROOT" && git grep -n -P '^-----BEGIN [A-Z0-9 ]*PRIVATE KEY-----$' -- . 2>/dev/null || true
)"

python3 - <<PY
import json
from datetime import datetime, timezone
from pathlib import Path

meta = {
    "artifactType": "ethicbit_transitional_key_rotation",
    "generatedAt": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    "mode": "transitional",
    "mldsaGenerationMode": "${mldsa_generation_mode}",
    "outputDir": "${OUTPUT_DIR}",
    "files": {
        "ed25519_private": "${ED25519_PRIV}",
        "ed25519_public": "${ED25519_PUB}",
        "mldsa_private": "${MLDSA_PRIV}",
        "mldsa_public": "${MLDSA_PUB}",
    },
    "trackedPrivateKeyHitsDetected": bool("${tracked_private_hits}".strip()),
}
Path("${META_PATH}").write_text(json.dumps(meta, indent=2, ensure_ascii=False) + "\\n", encoding="utf-8")
PY

echo
echo "Rotation bundle generated:"
echo "  ${OUTPUT_DIR}"
echo
echo "Suggested GitHub Secrets update commands:"
echo "  gh secret set ETHICBIT_ED25519_PRIVATE_KEY_PEM < \"${ED25519_PRIV}\""
echo "  gh secret set ETHICBIT_ED25519_PUBLIC_KEY_PEM  < \"${ED25519_PUB}\""
echo "  gh secret set ETHICBIT_MLDSA_PRIVATE_KEY_PEM   < \"${MLDSA_PRIV}\""
echo "  gh secret set ETHICBIT_MLDSA_PUBLIC_KEY_PEM    < \"${MLDSA_PUB}\""
echo
echo "Important:"
echo "  - This script does NOT rewrite git history."
echo "  - For historical purge, use a dedicated controlled script/process."

if [[ -n "${tracked_private_hits}" ]]; then
  echo
  echo "WARN: Potential tracked private key material detected in git content:"
  echo "${tracked_private_hits}"
  echo
  echo "Posture impact: NON_COMPLIANT until remediated."
fi

exit 0
