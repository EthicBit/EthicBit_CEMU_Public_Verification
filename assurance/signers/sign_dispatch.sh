#!/usr/bin/env bash
# Unified signer dispatcher for EthicBit.
# Supports:
#   - github_secrets_pem (local PEM signers)
#   - remote_signing_provider (HSM/KMS signing gateway)
#
# Usage:
#   sign_dispatch.sh <ALGORITHM> <PAYLOAD_FILE>
# Examples:
#   sign_dispatch.sh ED25519 provenance/payload.jcs.json
#   sign_dispatch.sh ML-DSA  provenance/payload.jcs.json
#
# Environment:
#   ETHICBIT_SIGNING_BACKEND=github_secrets_pem|remote_signing_provider
#
# Remote backend required env:
#   ETHICBIT_SIGNING_ENDPOINT
#   ETHICBIT_SIGNING_TOKEN
#   ETHICBIT_ED25519_KEY_ID
#   ETHICBIT_MLDSA_KEY_ID
#
# Optional remote env:
#   ETHICBIT_SIGNING_TIMEOUT_SECONDS (default: 30, max: 120)
#   ETHICBIT_SIGNING_CA_FILE
#   ETHICBIT_SIGNING_DISABLE_PROXY (default: 1)
#   ETHICBIT_SIGNING_INCLUDE_PAYLOAD_PATH (default: 0)
#   ETHICBIT_SIGNING_MAX_PAYLOAD_BYTES (default: 5242880)
#   ETHICBIT_SIGNING_MAX_RESPONSE_BYTES (default: 1048576)

set -euo pipefail
umask 077

usage() {
  echo "usage: $(basename "$0") <ALGORITHM> <PAYLOAD_FILE>" >&2
  exit 2
}

die() {
  echo "$*" >&2
  exit 1
}

require_executable() {
  local p="$1"
  [[ -x "$p" ]] || die "required executable not found: $p"
}

normalize_algorithm() {
  local raw="${1:-}"
  raw="$(printf '%s' "$raw" | tr '[:lower:]' '[:upper:]')"
  case "$raw" in
    ED25519)
      echo "ED25519"
      ;;
    ML-DSA|MLDSA)
      echo "ML-DSA"
      ;;
    *)
      die "unsupported algorithm: $1"
      ;;
  esac
}

validate_endpoint() {
  local endpoint="${1:-}"
  [[ -n "$endpoint" ]] || die "missing ETHICBIT_SIGNING_ENDPOINT"
  [[ "$endpoint" == https://* ]] || die "ETHICBIT_SIGNING_ENDPOINT must use https://"
  [[ "$endpoint" != *$'\n'* ]] || die "ETHICBIT_SIGNING_ENDPOINT contains invalid newline"
  [[ "$endpoint" != *$'\r'* ]] || die "ETHICBIT_SIGNING_ENDPOINT contains invalid carriage return"
}

[[ $# -eq 2 ]] || usage

ALG="$(normalize_algorithm "$1")"
PAYLOAD_FILE="$2"

[[ -f "$PAYLOAD_FILE" ]] || die "payload not found: $PAYLOAD_FILE"
[[ -r "$PAYLOAD_FILE" ]] || die "payload not readable: $PAYLOAD_FILE"

MAX_PAYLOAD_BYTES="${ETHICBIT_SIGNING_MAX_PAYLOAD_BYTES:-5242880}"
case "$MAX_PAYLOAD_BYTES" in
  ''|*[!0-9]*)
    die "ETHICBIT_SIGNING_MAX_PAYLOAD_BYTES must be numeric"
    ;;
esac

PAYLOAD_SIZE="$(wc -c < "$PAYLOAD_FILE" | tr -d '[:space:]')"
case "$PAYLOAD_SIZE" in
  ''|*[!0-9]*)
    die "could not determine payload size"
    ;;
esac
[[ "$PAYLOAD_SIZE" -le "$MAX_PAYLOAD_BYTES" ]] || die "payload exceeds max size (${MAX_PAYLOAD_BYTES} bytes)"

BACKEND="${ETHICBIT_SIGNING_BACKEND:-github_secrets_pem}"
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"

case "$BACKEND" in
  github_secrets_pem)
    case "$ALG" in
      ED25519)
        SIGNER="${SCRIPT_DIR}/ed25519_sign.sh"
        ;;
      ML-DSA)
        SIGNER="${SCRIPT_DIR}/mldsa_sign.sh"
        ;;
      *)
        die "unsupported algorithm for github_secrets_pem backend: $ALG"
        ;;
    esac
    require_executable "$SIGNER"
    exec "$SIGNER" "$PAYLOAD_FILE"
    ;;

  remote_signing_provider)
    ENDPOINT="${ETHICBIT_SIGNING_ENDPOINT:-}"
    TOKEN="${ETHICBIT_SIGNING_TOKEN:-}"
    [[ -n "$TOKEN" ]] || die "missing ETHICBIT_SIGNING_TOKEN"
    validate_endpoint "$ENDPOINT"

    case "$ALG" in
      ED25519)
        KEY_ID="${ETHICBIT_ED25519_KEY_ID:-}"
        ;;
      ML-DSA)
        KEY_ID="${ETHICBIT_MLDSA_KEY_ID:-}"
        ;;
      *)
        die "unsupported algorithm for remote_signing_provider backend: $ALG"
        ;;
    esac
    [[ -n "$KEY_ID" ]] || die "missing key id for algorithm ${ALG}"

    command -v python3 >/dev/null 2>&1 || die "python3 is required for remote_signing_provider backend"

    export ETHICBIT_DISPATCH_ALG="$ALG"
    export ETHICBIT_DISPATCH_KEY_ID="$KEY_ID"
    export ETHICBIT_DISPATCH_PAYLOAD_FILE="$PAYLOAD_FILE"
    export ETHICBIT_DISPATCH_ENDPOINT="$ENDPOINT"
    export ETHICBIT_DISPATCH_TOKEN="$TOKEN"
    export ETHICBIT_DISPATCH_TIMEOUT_SECONDS="${ETHICBIT_SIGNING_TIMEOUT_SECONDS:-30}"
    export ETHICBIT_DISPATCH_CA_FILE="${ETHICBIT_SIGNING_CA_FILE:-}"
    export ETHICBIT_DISPATCH_DISABLE_PROXY="${ETHICBIT_SIGNING_DISABLE_PROXY:-1}"
    export ETHICBIT_DISPATCH_INCLUDE_PAYLOAD_PATH="${ETHICBIT_SIGNING_INCLUDE_PAYLOAD_PATH:-0}"
    export ETHICBIT_DISPATCH_MAX_RESPONSE_BYTES="${ETHICBIT_SIGNING_MAX_RESPONSE_BYTES:-1048576}"

    python3 - <<'PY'
import base64
import binascii
import hashlib
import json
import os
import pathlib
import ssl
import urllib.error
import urllib.request


def as_bool(raw: str, default: bool = False) -> bool:
    v = str(raw or "").strip().lower()
    if v in {"1", "true", "yes", "y", "on"}:
        return True
    if v in {"0", "false", "no", "n", "off"}:
        return False
    return default


def parse_int(name: str, default: int, *, minimum: int, maximum: int) -> int:
    raw = os.environ.get(name, "")
    if not raw:
        return default
    try:
        value = int(raw)
    except ValueError as exc:
        raise SystemExit(f"{name} must be an integer") from exc
    if value < minimum or value > maximum:
        raise SystemExit(f"{name} must be between {minimum} and {maximum}")
    return value


alg = os.environ["ETHICBIT_DISPATCH_ALG"]
key_id = os.environ["ETHICBIT_DISPATCH_KEY_ID"]
payload_path = pathlib.Path(os.environ["ETHICBIT_DISPATCH_PAYLOAD_FILE"])
endpoint = os.environ["ETHICBIT_DISPATCH_ENDPOINT"].rstrip("/")
token = os.environ["ETHICBIT_DISPATCH_TOKEN"]
timeout_seconds = parse_int("ETHICBIT_DISPATCH_TIMEOUT_SECONDS", 30, minimum=1, maximum=120)
max_response_bytes = parse_int("ETHICBIT_DISPATCH_MAX_RESPONSE_BYTES", 1048576, minimum=256, maximum=16 * 1024 * 1024)
disable_proxy = as_bool(os.environ.get("ETHICBIT_DISPATCH_DISABLE_PROXY", "1"), default=True)
include_payload_path = as_bool(os.environ.get("ETHICBIT_DISPATCH_INCLUDE_PAYLOAD_PATH", "0"), default=False)
ca_file = os.environ.get("ETHICBIT_DISPATCH_CA_FILE", "").strip()

payload_bytes = payload_path.read_bytes()
payload_b64 = base64.b64encode(payload_bytes).decode("ascii")
payload_sha256 = hashlib.sha256(payload_bytes).hexdigest()

body_dict = {
    "algorithm": alg,
    "key_id": key_id,
    "payload_b64": payload_b64,
    "payload_sha256": payload_sha256,
}
if include_payload_path:
    body_dict["payload_path"] = str(payload_path)

body = json.dumps(body_dict, separators=(",", ":"), ensure_ascii=False).encode("utf-8")

req = urllib.request.Request(
    endpoint + "/sign",
    data=body,
    headers={
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    },
    method="POST",
)

context = ssl.create_default_context()
if ca_file:
    context.load_verify_locations(cafile=ca_file)

handlers = []
if disable_proxy:
    handlers.append(urllib.request.ProxyHandler({}))
handlers.append(urllib.request.HTTPSHandler(context=context))
opener = urllib.request.build_opener(*handlers)

try:
    with opener.open(req, timeout=timeout_seconds) as resp:
        raw = resp.read(max_response_bytes + 1)
except urllib.error.HTTPError as exc:
    msg = exc.read(4096).decode("utf-8", errors="replace")
    raise SystemExit(f"Remote signing HTTP error: {exc.code} {msg}") from exc
except Exception as exc:
    raise SystemExit(f"Remote signing request failed: {exc}") from exc

if len(raw) > max_response_bytes:
    raise SystemExit("Remote signing response exceeds maximum allowed size")

try:
    data = json.loads(raw.decode("utf-8"))
except Exception as exc:
    raise SystemExit(f"Remote signing returned invalid JSON: {exc}") from exc

signature = data.get("signature_b64") or data.get("signature")
if not isinstance(signature, str) or not signature.strip():
    raise SystemExit("Remote signing response missing signature_b64/signature")

signature = signature.strip()
try:
    base64.b64decode(signature, validate=True)
except (binascii.Error, ValueError) as exc:
    raise SystemExit("Remote signing response contains invalid base64 signature") from exc

print(signature, end="")
PY
    ;;

  *)
    die "unsupported signing backend: $BACKEND"
    ;;
esac
