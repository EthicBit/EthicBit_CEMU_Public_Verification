#!/usr/bin/env bash
set -euo pipefail
payload="$1"
sig_file="$2"
key_id="$3"
algorithm="$4"

: "${ETHICBIT_SIGNER_BASE_URL:?missing ETHICBIT_SIGNER_BASE_URL}"
: "${ETHICBIT_SIGNER_TOKEN:?missing ETHICBIT_SIGNER_TOKEN}"
CONNECT_TIMEOUT="${ETHICBIT_SIGNER_CONNECT_TIMEOUT_SEC:-5}"
MAX_TIME="${ETHICBIT_SIGNER_MAX_TIME_SEC:-15}"

payload_b64="$(base64 < "$payload" | tr -d '\n')"
sig="$(tr -d '\n' < "$sig_file")"

valid="$(curl -sSf -X POST "${ETHICBIT_SIGNER_BASE_URL}/verify" \
  --connect-timeout "${CONNECT_TIMEOUT}" \
  --max-time "${MAX_TIME}" \
  -H "Authorization: Bearer ${ETHICBIT_SIGNER_TOKEN}" \
  -H "Content-Type: application/json" \
  -d "{\"key_id\":\"${key_id}\",\"algorithm\":\"${algorithm}\",\"payload_b64\":\"${payload_b64}\",\"signature\":\"${sig}\"}" \
  | jq -r '.valid')"

[[ "${valid}" == "true" ]] || exit 2
