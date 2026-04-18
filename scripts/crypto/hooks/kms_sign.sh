#!/usr/bin/env bash
set -euo pipefail
payload="$1"
out_sig="$2"
key_id="$3"
algorithm="$4"

: "${ETHICBIT_SIGNER_BASE_URL:?missing ETHICBIT_SIGNER_BASE_URL}"
: "${ETHICBIT_SIGNER_TOKEN:?missing ETHICBIT_SIGNER_TOKEN}"
CONNECT_TIMEOUT="${ETHICBIT_SIGNER_CONNECT_TIMEOUT_SEC:-5}"
MAX_TIME="${ETHICBIT_SIGNER_MAX_TIME_SEC:-15}"

payload_b64="$(base64 < "$payload" | tr -d '\n')"

sig="$(curl -sSf -X POST "${ETHICBIT_SIGNER_BASE_URL}/sign" \
  --connect-timeout "${CONNECT_TIMEOUT}" \
  --max-time "${MAX_TIME}" \
  -H "Authorization: Bearer ${ETHICBIT_SIGNER_TOKEN}" \
  -H "Content-Type: application/json" \
  -d "{\"key_id\":\"${key_id}\",\"algorithm\":\"${algorithm}\",\"payload_b64\":\"${payload_b64}\"}" \
  | jq -r '.signature')"

[[ -n "${sig}" && "${sig}" != "null" ]] || { echo "signature missing"; exit 2; }
printf '%s\n' "${sig}" > "${out_sig}"
